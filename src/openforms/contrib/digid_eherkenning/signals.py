from django.db.models.signals import post_save
from django.dispatch import receiver

from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration

from .utils import create_digid_eherkenning_csp_settings


@receiver(post_save, sender=DigidConfiguration)
@receiver(post_save, sender=EherkenningConfiguration)
def trigger_csp_update(
    sender, instance: DigidConfiguration | EherkenningConfiguration, **kwargs
):
    create_digid_eherkenning_csp_settings(instance)
