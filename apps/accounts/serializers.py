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
