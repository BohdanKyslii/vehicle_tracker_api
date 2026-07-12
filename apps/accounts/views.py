from ctypes.macholib import framework

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf(reguest):
    """
        GET /api/auth/csrf/ — фронтенд викликає це ПЕРШИМ, ще до форми логіну,
        щоб браузер отримав csrftoken cookie (інакше перший POST впаде з 403).
        """
    return Response({'csrfToken': get_token(reguest)})

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """POST /api/auth/register/ — {username, email, password, role}"""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    # без login() — акаунт неактивний до підтвердження
    return Response(
        {"message": "Реєстрацію отримано. "
                    "Очікуйте підтвердження адміністратора."},
        status=201,
    )

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """POST /api/auth/login/ — {username, password}"""
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is None:
        # окремо перевіряємо: пароль міг бути правильним, просто акаунт ще не підтверджено
        pending = User.objects.filter(username=username, is_active=False).first()
        if pending and pending.check_password(password):
            return Response({"error": "Обліковий запис ще не підтверджено адміністратором"}, status=403)
        return Response({"error": "Неправильний логін або пароль."}, status=400)
    login(request, user)
    return Response(UserSerializer(user).data)

@api_view(['POST'])
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