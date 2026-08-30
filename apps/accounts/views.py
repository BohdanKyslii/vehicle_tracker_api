import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.middleware.csrf import get_token
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Profile
from .notifications import notify_admin_new_registration
from .permissions import IsHeadOnly
from .serializers import AdminUserSerializer, RegisterSerializer, UserSerializer
from .telegram_auth import InitDataError, verify_init_data


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(reguest):
    """
    GET /api/auth/csrf/ — фронтенд викликає це ПЕРШИМ, ще до форми логіну,
    щоб браузер отримав csrftoken cookie (інакше перший POST впаде з 403).
    """
    return Response({"csrfToken": get_token(reguest)})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """POST /api/auth/register/ — {username, email, password, role}"""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    # без login() — акаунт неактивний до підтвердження
    notify_admin_new_registration(user)
    return Response(
        {"message": "Реєстрацію отримано. Очікуйте підтвердження адміністратора."},
        status=201,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """POST /api/auth/login/ — {username, password}"""
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is None:
        # окремо перевіряємо: пароль міг бути правильним, просто акаунт ще не підтверджено
        pending = User.objects.filter(username=username, is_active=False).first()
        if pending and pending.check_password(password):
            return Response(
                {"error": "Обліковий запис ще не підтверджено адміністратором"},
                status=403,
            )
        return Response({"error": "Неправильний логін або пароль."}, status=400)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    """POST /api/auth/logout/"""
    logout(request)
    return Response(status=204)


@api_view(["GET"])
@permission_classes([AllowAny])
def me(request):
    """
    GET /api/auth/me/ — поточний користувач.
    Фронтенд викликає це при завантаженні застосунку, щоб дізнатись,
    чи є активна сесія (замість того, щоб зберігати щось у localStorage).
    """
    if not request.user.is_authenticated:
        return Response({"user": None})
    return Response({"user": UserSerializer(request.user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def telegram_login(request):
    """POST /api/auth/telegram/ — {"initData": "<window.Telegram.WebApp.initData>"}"""
    try:
        data = verify_init_data(
            request.data.get("initData", ""), settings.TELEGRAM_BOT_TOKEN
        )
        telegram_id = json.loads(data["user"])["id"]
    except (InitDataError, KeyError, ValueError):
        return Response({"error": "invalid_init_data"}, status=400)

    profile = (
        Profile.objects.filter(telegram_id=telegram_id).select_related("user").first()
    )
    if profile is None:
        return Response({"error": "not_registered"}, status=404)
    if not profile.user.is_active:
        return Response({"error": "pending_approval"}, status=403)

    login(request, profile.user)
    return Response(UserSerializer(profile.user).data)


class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/users/ — панель керування користувачами (лише head): підтвердження
    заявок (PATCH is_active=true разом з role), зміна ролі, відхилення
    заявки (DELETE), відв'язка/перегляд Telegram. Навмисно без CreateModelMixin
    — акаунти створюються лише через /auth/register/ або бот, не тут.
    profile__isnull=False виключає "сирі" Django-суперюзери (вхід у /admin/),
    що не мають Profile і не є частиною доменної рольової моделі застосунку.
    """

    queryset = (
        User.objects.filter(profile__isnull=False)
        .select_related("profile", "profile__driver")
        .order_by("-date_joined")
    )
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsHeadOnly]

    def perform_destroy(self, instance):
        # Дозволяємо видаляти лише непідтверджені заявки (та сама умова, що
        # bot.py::_reject_user) — щоб випадкове натискання не знесло вже
        # робочий акаунт замість того, щоб просто деактивувати його.
        if instance.is_active:
            raise ValidationError({"error": "Можна відхилити лише непідтверджену заявку. Активного користувача деактивуйте (is_active=false), не видаляйте."})
        instance.delete()

    @action(detail=True, methods=["post"], url_path="link-telegram")
    def link_telegram(self, request, pk=None):
        """
        POST /api/users/{id}/link-telegram/ — {"sourceUserId": <id>}
        Переносить profile.telegram_id із джерела на цей (уже наявний
        email-)акаунт. Джерело обмежене саме непідтвердженою Telegram-
        заявкою (is_active=False, username "tg_<id>") — навмисно, а не
        будь-яким акаунтом із telegram_id: об'єднання з довільним АКТИВНИМ
        акаунтом непередбачувано зачепило б і його Driver/картку водія.
        """
        target = self.get_object()
        source_id = request.data.get("sourceUserId")
        try:
            source = User.objects.select_related("profile", "profile__driver").get(id=source_id)
        except (User.DoesNotExist, TypeError, ValueError):
            return Response({"error": "Заявку-джерело не знайдено"}, status=404)

        if source.id == target.id:
            return Response({"error": "Не можна об'єднати користувача із самим собою"}, status=400)
        if source.is_active or not source.username.startswith("tg_"):
            return Response(
                {"error": "Об'єднати можна лише з непідтвердженою Telegram-заявкою (tg_...)"},
                status=400,
            )
        if target.profile.telegram_id:
            return Response({"error": "У цього користувача вже прив'язано Telegram"}, status=400)

        with transaction.atomic():
            target.profile.telegram_id = source.profile.telegram_id
            if target.profile.driver_id is None and source.profile.driver_id is not None:
                target.profile.driver = source.profile.driver
            target.profile.save(update_fields=["telegram_id", "driver"])
            source.delete()  # каскадом видаляє й Profile-заявку джерела

        return Response(AdminUserSerializer(target).data)
