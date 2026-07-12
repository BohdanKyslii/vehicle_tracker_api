# Права доступу за роллю — маленький helper
from rest_framework.permissions import BasePermission

class HasRole(BasePermission):
    allowed_roles = ()
    def has_permission(self, request, view):
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role in self.allowed_roles)

class IsManagerOrHead(HasRole):
    allowed_roles = ('manager', 'head')