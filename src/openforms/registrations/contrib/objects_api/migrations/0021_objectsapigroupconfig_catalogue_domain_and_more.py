# Generated by Django 4.2.14 on 2024-08-01 06:42

from django.db import migrations, models

import openforms.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ("registrations_objects_api", "0020_objecttype_url_to_uuid"),
    ]

    operations = [
        migrations.AddField(
            model_name="objectsapigroupconfig",
            name="catalogue_domain",
            field=models.CharField(
                blank=True,
                help_text="The 'domein' attribute for the Catalogus resource in the Catalogi API.",
                max_length=5,
                verbose_name="catalogus domain",
            ),
        ),
        migrations.AddField(
            model_name="objectsapigroupconfig",
            name="catalogue_rsin",
            field=models.CharField(
                blank=True,
                help_text="The 'rsin' attribute for the Catalogus resource in the Catalogi API.",
                max_length=9,
                validators=[openforms.utils.validators.RSINValidator()],
                verbose_name="catalogus RSIN",
            ),
        ),
        migrations.AddConstraint(
            model_name="objectsapigroupconfig",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(("catalogue_domain", ""), ("catalogue_rsin", "")),
                    models.Q(
                        models.Q(("catalogue_domain", ""), _negated=True),
                        models.Q(("catalogue_rsin", ""), _negated=True),
                    ),
                    _connector="OR",
                ),
                name="catalogue_composite_key",
                violation_error_message="You must specify both domain and RSIN to uniquely identify a catalogue.",
            ),
        ),
    ]
