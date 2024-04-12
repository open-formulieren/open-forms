# Generated by Django 4.2.11 on 2024-04-12 10:08

from django.db import migrations, models
import openforms.payments.validators


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0056_globalconfiguration_enable_backend_formio_validation"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="payment_order_id_template",
            field=models.CharField(
                default="{year}/{reference}/{uid}",
                help_text="Template to use when generating payment order IDs. It should be alpha-numerical and can contain the '/._-' characters. The following placeholders are supported:\n  - {year}: The current year\n  - {reference}: The submission reference\n  - {uid}: A unique incrementing payment ID.",
                max_length=48,
                validators=[
                    openforms.payments.validators.validate_payment_order_id_template
                ],
                verbose_name="Payment Order ID template",
            ),
        ),
    ]
