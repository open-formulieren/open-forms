from django_setup_configuration.configuration import BaseConfigurationStep
from zgw_consumers.models import Service

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig

from .models import ObjectsAPIGroupConfigModel, SingleObjectsAPIGroupConfigModel


def get_service(slug: str) -> Service:
    """
    Try to find a Service and re-raise DoesNotExist with the identifier to make debugging
    easier
    """
    try:
        return Service.objects.get(slug=slug)
    except Service.DoesNotExist as e:
        raise Service.DoesNotExist(f"{str(e)} (identifier = {slug})")


class ObjectsAPIConfigurationStep(BaseConfigurationStep[ObjectsAPIGroupConfigModel]):
    """
    Configure groups for the Objects API backend. This step uses identifiers to refer to
    Services that should be loaded by the previous step that loads Services.
    """

    verbose_name = "Configuration to set up Objects API registration backend services"
    config_model = ObjectsAPIGroupConfigModel
    namespace = "objects_api"
    enable_setting = "objects_api_config_enable"

    def execute(self, model: ObjectsAPIGroupConfigModel):
        config: SingleObjectsAPIGroupConfigModel
        for config in model.groups:
            # setup_configuration typing doesn't work for `django_model_refs` yet,
            # hence the type: ignores
            # (https://github.com/maykinmedia/django-setup-configuration/issues/25)
            defaults = {
                "name": config.name,  # type: ignore
                "objects_service": get_service(config.objects_service_identifier),
                "objecttypes_service": get_service(
                    config.objecttypes_service_identifier
                ),
                "organisatie_rsin": config.organisatie_rsin,  # type: ignore
            }
            if config.documenten_service_identifier:
                defaults["drc_service"] = get_service(
                    config.documenten_service_identifier
                )
            if config.catalogi_service_identifier:
                defaults["catalogi_service"] = get_service(
                    config.catalogi_service_identifier
                )

            ObjectsAPIGroupConfig.objects.update_or_create(
                identifier=config.identifier,  # type: ignore
                defaults=defaults,
            )
