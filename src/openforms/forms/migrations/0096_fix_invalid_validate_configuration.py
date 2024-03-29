# Generated by Django 4.2.10 on 2024-03-15 16:02

from django.db import migrations

from openforms.forms.migration_operations import ConvertComponentsOperation


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0095_merge_20240313_1742"),
    ]

    operations = [
        ConvertComponentsOperation("textfield", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("email", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("phoneNumber", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("postcode", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("textarea", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("number", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("currency", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("iban", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("licenseplate", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("bsn", "fix_empty_validate_lengths"),
        ConvertComponentsOperation("cosign", "fix_empty_validate_lengths"),
    ]
