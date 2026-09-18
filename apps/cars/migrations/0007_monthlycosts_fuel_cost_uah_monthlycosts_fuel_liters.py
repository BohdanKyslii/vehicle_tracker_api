from django.db import migrations, models


class Migration(migrations.Migration):
    # Залежність саме від 0005, а НЕ від локального
    # 0006_alter_car_amount_car_... — той файл згенерувався як шум
    # (порожні AlterField через розбіжність версії Django), лишився
    # untracked і в репо/проді його немає.
    dependencies = [
        ("cars", "0005_car_status_pause_downtime"),
    ]

    operations = [
        migrations.AddField(
            model_name="monthlycosts",
            name="fuel_cost_uah",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Пальне за місяць (грн)",
                max_digits=10,
                verbose_name="Пальне (грн)",
            ),
        ),
        migrations.AddField(
            model_name="monthlycosts",
            name="fuel_liters",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Пальне за місяць (л) — довідково, у вартість не входить",
                max_digits=10,
                verbose_name="Пальне (л)",
            ),
        ),
    ]
