# Generated by Django 4.2.11 on 2024-09-20 09:02

from django.db import migrations

from ..migration_operations import ConvertComponentsOperation


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0096_fix_invalid_validate_configuration"),
    ]

    operations = [
        ConvertComponentsOperation(
            "file", "ensure_extra_zip_mimetypes_exist_in_file_type"
        ),
    ]
