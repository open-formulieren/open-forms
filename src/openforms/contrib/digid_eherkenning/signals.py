from django.db.models.signals import post_save
from django.dispatch import receiver

from digid_eherkenning.models.digid import DigidConfiguration
from digid_eherkenning.models.eherkenning import EherkenningConfiguration

from openforms.contrib.digid_eherkenning.utils import (
    create_digid_eherkenning_csp_settings,
)

from .constants import CONFIG_TYPES


@receiver(post_save, sender=DigidConfiguration)
@receiver(post_save, sender=EherkenningConfiguration)
def trigger_csp_update(
    sender, instance: DigidConfiguration | EherkenningConfiguration, **kwargs
):
    create_digid_eherkenning_csp_settings(instance, CONFIG_TYPES[type(instance)])
