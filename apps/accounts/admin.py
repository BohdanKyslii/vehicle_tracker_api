from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile

class ProfileInLine(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Профіль"

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInLine,)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("username",)
        return self.readonly_fields

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
