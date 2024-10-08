# Generated by Django 4.2.16 on 2024-09-09 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0098_form_introduction_page_content_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="form",
            name="show_summary_progress",
            field=models.BooleanField(
                default=False,
                help_text="Whether to display the short progress summary, indicating the current step number and total amount of steps.",
                verbose_name="show summary of the progress",
            ),
        ),
    ]
