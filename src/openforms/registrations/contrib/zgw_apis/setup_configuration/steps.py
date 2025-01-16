from django_setup_configuration.configuration import BaseConfigurationStep
from zgw_consumers.models import Service

from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig

from .models import SingleZGWApiGroupConfigModel, ZGWApiGroupConfigModel


def get_service(slug: str) -> Service:
    """
    Try to find a Service and re-raise DoesNotExist with the identifier to make debugging
    easier
    """
    try:
        return Service.objects.get(slug=slug)
    except Service.DoesNotExist as e:
        raise Service.DoesNotExist(f"{str(e)} (identifier = {slug})")


class ZGWApiConfigurationStep(BaseConfigurationStep[ZGWApiGroupConfigModel]):
    """
    Configure groups for the ZGW APIs registration backend. This step uses identifiers to refer to
    Services that should be loaded by the previous step that loads Services.
    """

    verbose_name = "Configuration to set up ZGW API registration backend services"
    config_model = ZGWApiGroupConfigModel
    namespace = "zgw_api"
    enable_setting = "zgw_api_config_enable"

    def execute(self, model: ZGWApiGroupConfigModel):
        config: SingleZGWApiGroupConfigModel
        for config in model.groups:
            # setup_configuration typing doesn't work for `django_model_refs` yet,
            # hence the type: ignores
            # (https://github.com/maykinmedia/django-setup-configuration/issues/25)
            defaults = {
                "name": config.name,  # type: ignore
                "zrc_service": get_service(config.zaken_service_identifier),
                "drc_service": get_service(config.documenten_service_identifier),
                "ztc_service": get_service(config.catalogi_service_identifier),
                "catalogue_domain": config.catalogue_domain,  # type: ignore
                "catalogue_rsin": config.catalogue_rsin,  # type: ignore
                "organisatie_rsin": config.organisatie_rsin,  # type: ignore
                "zaak_vertrouwelijkheidaanduiding": config.zaak_vertrouwelijkheidaanduiding,  # type: ignore
                "doc_vertrouwelijkheidaanduiding": config.doc_vertrouwelijkheidaanduiding,  # type: ignore
                "auteur": config.auteur,  # type: ignore
                "content_json": config.objects_api_json_content_template,
            }

            ZGWApiGroupConfig.objects.update_or_create(
                identifier=config.identifier,  # type: ignore
                defaults=defaults,
            )
