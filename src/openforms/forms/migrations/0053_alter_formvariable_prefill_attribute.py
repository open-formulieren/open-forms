# Generated by Django 3.2.15 on 2023-01-18 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0052_fix_rules_with_selectboxes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="formvariable",
            name="prefill_attribute",
            field=models.CharField(
                blank=True,
                help_text="Which attribute from the prefill response should be used to fill this variable",
                max_length=200,
                verbose_name="prefill attribute",
            ),
        ),
    ]