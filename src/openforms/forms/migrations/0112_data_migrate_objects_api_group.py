from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "forms",
            "0111_formvariable_form_variable_subtype_empty_iff_data_type_is_not_array_and_more",
        ),
        ("objects_api", "0006_alter_objectsapigroupconfig_catalogue_domain"),
    ]

    # Emptied as part of the 3.4 release cycle - they're guaranteed to have been
    # executed on 3.3.x.
    operations = []
