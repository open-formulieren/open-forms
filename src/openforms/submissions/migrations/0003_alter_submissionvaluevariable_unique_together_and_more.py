# Generated by Django 4.2.18 on 2025-02-03 13:23

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0002_v230_to_v300"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="submissionvaluevariable",
            unique_together={("submission", "key")},
        ),
        migrations.RemoveField(
            model_name="submissionvaluevariable",
            name="form_variable",
        ),
    ]
