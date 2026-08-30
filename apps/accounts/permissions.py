# Права доступу за роллю — маленький helper
from rest_framework.permissions import BasePermission

class HasRole(BasePermission):
    allowed_roles = ()
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role in self.allowed_roles)

class IsManagerOrHead(HasRole):
    allowed_roles = ('manager', 'head', "logist")

class IsLogistOrAbove(HasRole):
    allowed_roles = ('logist', 'manager', 'head')

class IsHeadOnly(HasRole):
    """
    Лише head, без 'menedzher/logist' — на відміну від IsManagerOrHead.
    Для операцій, де розширений доступ був би зміною прав доступу самих
    користувачів (ролі, підтвердження реєстрацій, Telegram-лінкування).
    """
    allowed_roles = ('head',)
