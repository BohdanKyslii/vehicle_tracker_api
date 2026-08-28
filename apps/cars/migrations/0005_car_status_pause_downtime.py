# Ручна міграція — навмисно ТІЛЬКИ status_car.choices, а не автогенерація
# makemigrations (та тягне за собою ~80 незв'язаних "Alter field" по всіх
# моделях — накопичена розбіжність verbose_name/help_text без міграцій,
# що існувала до цієї зміни; чіпати те все тут — poза межами задачі).
#
# choices на CharField — суто Django-валідація, без DB CHECK-обмеження,
# тож ця міграція не змінює жодного реального стовпця в Postgres.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cars", "0004_fix_trailer_schema_drift"),
    ]

    operations = [
        migrations.AlterField(
            model_name="car",
            name="status_car",
            field=models.CharField(
                choices=[
                    ("active", "Активне"),
                    ("repair", "Ремонт"),
                    ("inactive", "Неактивне"),
                    ("pause", "Пауза"),
                    ("driver_downtime", "Простій (водій)"),
                ],
                default="active",
                help_text="Статус",
                max_length=20,
                verbose_name="Статус",
            ),
        ),
    ]
