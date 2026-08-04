import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Profile
from .notifications import notify_admin_new_registration
from .serializers import RegisterSerializer, UserSerializer
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
