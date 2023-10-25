from django.db.models.signals import post_save
from django.dispatch import receiver

from digid_eherkenning.models.digid import DigidConfiguration

from openforms.config.utils import create_digid_eherkenning_csp_settings


@receiver(post_save, sender=DigidConfiguration)
def trigger_csp_update(sender, instance, **kwargs):
    create_digid_eherkenning_csp_settings(instance, "digid")
