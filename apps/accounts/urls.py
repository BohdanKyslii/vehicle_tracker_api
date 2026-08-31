from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"users", views.AdminUserViewSet, basename="users")

urlpatterns = [
    path("auth/csrf/", views.csrf),
    path("auth/register/", views.register),
    path("auth/login/", views.login_view),
    path("auth/logout/", views.logout_view),
    path("auth/me/", views.me),
    path("auth/telegram/", views.telegram_login),
] + router.urls
