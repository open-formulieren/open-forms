# Generated by Django 2.2.20 on 2021-05-06 10:36

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0009_auto_20210426_1802"),
    ]

    operations = [
        migrations.AlterField(
            model_name="form",
            name="slug",
            field=autoslug.fields.AutoSlugField(max_length=100, unique=True),
        ),
    ]
