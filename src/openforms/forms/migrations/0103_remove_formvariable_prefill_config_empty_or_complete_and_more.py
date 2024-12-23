# Generated by Django 4.2.16 on 2024-10-23 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0102_merge_20241022_1143"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="formvariable",
            name="prefill_config_empty_or_complete",
        ),
        migrations.AddField(
            model_name="formvariable",
            name="prefill_options",
            field=models.JSONField(
                blank=True, default=dict, verbose_name="prefill options"
            ),
        ),
        migrations.AddConstraint(
            model_name="formvariable",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        models.Q(
                            ("prefill_plugin", ""),
                            ("prefill_attribute", ""),
                            ("prefill_options", {}),
                        ),
                        models.Q(
                            models.Q(("prefill_plugin", ""), _negated=True),
                            ("prefill_attribute", ""),
                            models.Q(("prefill_options", {}), _negated=True),
                            ("source", "user_defined"),
                        ),
                        models.Q(
                            models.Q(("prefill_plugin", ""), _negated=True),
                            models.Q(("prefill_attribute", ""), _negated=True),
                            ("prefill_options", {}),
                        ),
                        _connector="OR",
                    )
                ),
                name="prefill_config_component_or_user_defined",
            ),
        ),
    ]
