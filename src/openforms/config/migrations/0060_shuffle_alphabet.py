from random import sample

from django.db import migrations
from django.db.migrations.state import StateApps


def shuffle_alphabet(apps: StateApps, _):
    """
    Shuffle public_reference_alphabet to make generated ids unique across different instances.
    """
    GlobalConfiguration = apps.get_model("config", "GlobalConfiguration")
    config, _ = GlobalConfiguration.objects.get_or_create()
    shuffled_alphabet = "".join(
        sample(config.public_reference_alphabet, len(config.public_reference_alphabet))
    )
    config.public_reference_alphabet = shuffled_alphabet
    config.save(update_fields=["public_reference_alphabet"])


class Migration(migrations.Migration):
    dependencies = [
        (
            "config",
            "0059_globalconfiguration_public_reference_alphabet_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            shuffle_alphabet,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
