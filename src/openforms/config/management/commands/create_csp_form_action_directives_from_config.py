from django.core.management import BaseCommand

from digid_eherkenning.models import DigidConfiguration, EherkenningConfiguration

from openforms.payments.contrib.ogone.models import OgoneMerchant


class Command(BaseCommand):
    help = (
        "Introspect the runtime configuration and generate the relevant CSP "
        "form-action directives"
    )

    def handle(self, **options):
        ogone_merchants = OgoneMerchant.objects.exclude(
            endpoint_preset="",
            endpoint_custom="",
        )
        for ogone_merchant in ogone_merchants:
            ogone_merchant.save()  # triggers CSPSetting record creation

        for model_cls in (DigidConfiguration, EherkenningConfiguration):
            configured_instance = model_cls.objects.exclude(
                idp_metadata_file=""
            ).first()
            if configured_instance is None:
                continue

            configured_instance.save()  # triggers CSPSetting record creation
