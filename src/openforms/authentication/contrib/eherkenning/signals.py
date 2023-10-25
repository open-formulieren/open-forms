from django.db.models.signals import post_save
from django.dispatch import receiver

from digid_eherkenning.models.eherkenning import EherkenningConfiguration

from openforms.config.utils import create_digid_eherkenning_csp_settings


@receiver(post_save, sender=EherkenningConfiguration)
def trigger_csp_update(sender, instance, **kwargs):
    create_digid_eherkenning_csp_settings(instance, "eherkenning")
