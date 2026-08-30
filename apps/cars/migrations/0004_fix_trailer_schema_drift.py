# Ручна міграція — виправляє розбіжність між models.py і фактичною схемою БД.
#
# Historically Trailer.model (обов'язкове поле) було замінено на
# name_trailer/vin_code прямо в models.py, БЕЗ makemigrations — тож
# міграції й досі "думають", що є лише `model` (з 0001_initial), а БД
# фактично вже має і name_trailer, і vin_code (додані десь поза
# міграціями), і досі має орфанну колонку `model` NOT NULL без дефолту.
# Через це INSERT в trailers завжди падав з IntegrityError, щойно
# водій/логіст пробував створити авто з причепом (created_at
# частково комітився — Car/CarSpecs вже в БД, Trailer — ні, бо
# CarSerializer.create() не був атомарним — див. sibling-фікс у
# serializers.py).
#
# SeparateDatabaseAndState: стан (для makemigrations) синхронізуємо з
# models.py напряму; SQL — ідемпотентний (IF EXISTS/IF NOT EXISTS), щоб
# однаково безпечно відпрацював і там, де стовпці вже додані вручну
# (як тут, локально), і там, де фактична схема могла піти іншим шляхом.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cars", "0003_remove_driver_telegram_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="trailer",
                    name="model",
                ),
                migrations.AddField(
                    model_name="trailer",
                    name="name_trailer",
                    field=models.CharField(
                        max_length=150,
                        blank=True,
                        default="",
                        verbose_name="Назва причепа",
                    ),
                ),
                migrations.AddField(
                    model_name="trailer",
                    name="vin_code",
                    field=models.CharField(
                        max_length=17,
                        blank=True,
                        default="",
                        verbose_name="VIN код",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'trailers' AND column_name = 'name_trailer'
                        ) THEN
                            ALTER TABLE trailers
                                ADD COLUMN name_trailer varchar(150) NOT NULL DEFAULT '';
                        END IF;

                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'trailers' AND column_name = 'vin_code'
                        ) THEN
                            ALTER TABLE trailers
                                ADD COLUMN vin_code varchar(17) NOT NULL DEFAULT '';
                        END IF;

                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name = 'trailers' AND column_name = 'model'
                        ) THEN
                            ALTER TABLE trailers ALTER COLUMN model DROP NOT NULL;
                            ALTER TABLE trailers DROP COLUMN model;
                        END IF;
                    END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
