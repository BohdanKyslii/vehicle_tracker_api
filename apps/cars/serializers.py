from django.db import transaction
from rest_framework import serializers

from .models import Car, CarSpecs, CarStatusLog, Driver, MonthlyCosts, RouteEvent, Trailer


class CarSpecsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarSpecs
        exclude = ["id", "car"]


class TrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trailer
        exclude = ["id", "car"]


class CarSerializer(serializers.ModelSerializer):
    specs = CarSpecsSerializer(read_only=False)
    # required=False — фронтенд надсилає "trailer" лише коли hasTrailer=true;
    # без цього DRF вважає вкладений серіалізатор обов'язковим і відхиляє
    # створення авто без причепа з 400 "This field is required."
    trailer = TrailerSerializer(read_only=False, required=False, allow_null=True)
    # source — звідки брати значення
    driver_name = serializers.CharField(
        source="driver.name_driver",
        read_only=True,
    )

    class Meta:
        model = Car
        fields = [
            "id",
            "name_car",
            "number_car",
            "fuel_card_number",
            "amount_car",
            "default_tracking_mode",
            "status_car",
            "is_active",
            "specs",
            "trailer",
            "driver_name",
        ]

    # transaction.atomic() — без цього падіння на Trailer/CarSpecs (напр.
    # IntegrityError) лишало вже створений Car в БД напівготовим: наступна
    # спроба з тим самим номером падала на "вже існує", хоча по факту
    # авто так і не було коректно створено жодного разу
    @transaction.atomic
    def create(self, validated_data):
        specs_data = validated_data.pop("specs", None)
        trailer_data = validated_data.pop("trailer", None)
        car = Car.objects.create(**validated_data)
        if specs_data:
            CarSpecs.objects.create(car=car, **specs_data)
        if trailer_data:
            Trailer.objects.create(car=car, **trailer_data)
        return car

    @transaction.atomic
    def update(self, instance, validated_data):
        specs_data = validated_data.pop("specs", None)
        trailer_data = validated_data.pop("trailer", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if specs_data is not None:
            CarSpecs.objects.update_or_create(car=instance, defaults=specs_data)
        if trailer_data is not None:
            Trailer.objects.update_or_create(car=instance, defaults=trailer_data)
        return instance


class DriverSerializer(serializers.ModelSerializer):
    car_number = serializers.CharField(
        source="car.number_car",
        read_only=True,
    )
    car_name = serializers.CharField(
        source="car.name_car",
        read_only=True,
    )

    class Meta:
        model = Driver
        fields = [
            "id",
            "name_driver",
            "phone",
            "car",
            "car_number",
            "car_name",
            "is_active",
        ]


class RouteEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteEvent
        fields = "__all__"  # всі поля


class RouteEventCreateSerializer(serializers.ModelSerializer):
    """Серіалізатор для створення події — без id і created_at."""

    class Meta:
        model = RouteEvent
        exclude = ["id", "created_at"]


class MonthlyCostsSerializer(serializers.ModelSerializer):
    car_number = serializers.CharField(
        source="car.number_car",
        read_only=True,
    )
    repair_cost_uah = serializers.SerializerMethodField()
    total_cost_uah = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyCosts
        fields = [
            "id",
            "car",
            "car_number",
            "month",
            "salary_uah",
            "taxes_uah",
            "depreciation_uah",
            "repair_actual_uah",
            "repair_rate_uah_km",
            "fuel_cost_uah",
            "fuel_liters",
            "other_costs_uah",
            "other_costs_comment",
            "repair_cost_uah",
            "total_cost_uah",
        ]

    def get_repair_cost_uah(self, obj):
        """Повертає фактичні або розраховані витрати на ремонт."""
        if obj.repair_actual_uah is not None:
            return float(obj.repair_actual_uah)
        # Потрібен загальний пробіг — передається через context
        total_km = self.context.get("total_km", 0)
        return float(obj.repair_rate_uah_km) * total_km

    def get_total_cost_uah(self, obj):
        """
        Разом = ЗП + податки + амортизація + пальне + інші + ремонт.
        Літри (fuel_liters) — довідкові, у гривневу суму не входять.
        """
        repair = self.get_repair_cost_uah(obj)
        return (
            float(
                obj.salary_uah
                + obj.taxes_uah
                + obj.depreciation_uah
                + obj.fuel_cost_uah
                + obj.other_costs_uah
            )
            + repair
        )


class CarStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarStatusLog
        fields = ["id", "car", "status", "reason", "changed_at", "changed_by"]
        read_only_fields = ["changed_at"]
