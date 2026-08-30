from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import Profile
from apps.cars.models import Driver


class RegisterSerializer(serializers.ModelSerializer):
    # write_only — це поле приймається на вхід, але ніколи не повертається у відповіді
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    # HEAD ("Керівник") призначається лише вручну через admin — не при самореєстрації
    role = serializers.ChoiceField(
        choices=[c for c in Profile.Role.choices if c[0] != Profile.Role.HEAD],
        write_only=True,
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "role")

    def create(self, validated_data):
        role = validated_data.pop("role")
        # неактивний, поки адміністратор не підтвердить
        # create_user — хешує пароль (звичайний create() зберіг би його як є)
        with transaction.atomic():
            user = User.objects.create_user(**validated_data, is_active=False)
            driver = None
            if role == Profile.Role.DRIVER:
                # Email-реєстрація не питає ПІБ/телефон (на відміну від
                # Telegram-боту, bot.py::_create_driver_registration) —
                # створюємо порожню картку одразу, щоб бот/адмін могли
                # закріпити авто без походу в Django Admin; ПІБ/телефон/
                # посвідчення дописує адмін пізніше через /fleet/drivers/<id>.
                driver = Driver.objects.create(name_driver=user.username)
            Profile.objects.create(user=user, role=role, driver=driver)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("role", "phone", "telegram_id", "driver")


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active", "profile")


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Для /api/users/ (панель head — apps.accounts.views.AdminUserViewSet).
    role — джерело `profile.role`: DRF сам розгортає його в
    validated_data["profile"]["role"] завдяки dotted source, тож PATCH
    {"role": "...", "is_active": true} апрувить заявку одним запитом,
    тим самим, що робить бот у _approve_user (bot.py).
    """

    role = serializers.ChoiceField(source="profile.role", choices=Profile.Role.choices, required=False)
    phone = serializers.CharField(source="profile.phone", read_only=True)
    telegram_id = serializers.IntegerField(source="profile.telegram_id", read_only=True, allow_null=True)
    driver_id = serializers.IntegerField(source="profile.driver_id", read_only=True, allow_null=True)
    driver_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "is_active", "date_joined",
            "role", "phone", "telegram_id", "driver_id", "driver_name",
        )
        read_only_fields = ("username", "email", "date_joined")

    def get_driver_name(self, obj):
        driver = getattr(obj.profile, "driver", None)
        return driver.name_driver if driver else None

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        instance = super().update(instance, validated_data)
        if "role" in profile_data:
            instance.profile.role = profile_data["role"]
            instance.profile.save(update_fields=["role"])
        return instance
