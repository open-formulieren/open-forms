# Generated by Django 2.2.10 on 2020-09-17 08:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("zgw_consumers", "0010_nlxconfig"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="service",
            name="extra",
        ),
    ]
