import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cars", "0005_car_status_pause_downtime"),
        ("waybills", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="waybillrecord",
            name="assigned_car",
            field=models.ForeignKey(
                blank=True,
                help_text="Авто власного парку для каналу 'Власне авто'",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_waybill_records",
                to="cars.car",
                verbose_name="Призначене авто",
            ),
        ),
        migrations.AddField(
            model_name="waybillrecord",
            name="carrier_ttn",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Номер ТТН для каналу 'Служба доставки'",
                max_length=50,
                verbose_name="ТТН служби доставки",
            ),
        ),
        migrations.AddField(
            model_name="waybillrecord",
            name="hired_car_number",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Держ. номер найманого авто для каналу 'Найманий транспорт'",
                max_length=20,
                verbose_name="Номер авто (найманий транспорт)",
            ),
        ),
    ]
