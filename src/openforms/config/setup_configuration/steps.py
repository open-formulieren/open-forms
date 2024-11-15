from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import SelfTestFailed
from zgw_consumers.models import Service

from openforms.contrib.objects_api.clients import get_catalogi_client
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig

from .models import ObjectsAPIGroupConfigModel


class ObjectsAPIConfigurationStep(BaseConfigurationStep[ObjectsAPIGroupConfigModel]):
    """
    Configure admin login via OpenID Connect
    """

    verbose_name = "Configuration to set up Objects API registration backend services"
    config_model = ObjectsAPIGroupConfigModel
    namespace = "OBJECTS_API"
    enable_setting = "OBJECTS_API_CONFIG_ENABLE"

    def is_configured(self, model: ObjectsAPIGroupConfigModel) -> bool:
        names = [config.name for config in model.groups]
        return ObjectsAPIGroupConfig.objects.filter(name__in=names).count() == len(
            names
        )

    def execute(self, model: ObjectsAPIGroupConfigModel):
        for config in model.groups:
            # TODO add proper error handling for service.get and optimize queries?
            # TODO is it correct to override everything?
            ObjectsAPIGroupConfig.objects.update_or_create(
                name=config.name,
                defaults={
                    "objects_service": Service.objects.get(
                        slug=config.objects_service_slug
                    ),
                    "objecttypes_service": Service.objects.get(
                        slug=config.objecttypes_service_slug
                    ),
                    "drc_service": Service.objects.get(slug=config.drc_service_slug),
                    "catalogi_service": Service.objects.get(
                        slug=config.catalogi_service_slug
                    ),
                    "catalogue_domain": config.catalogue_domain,
                    "catalogue_rsin": config.catalogue_rsin,
                    "organisatie_rsin": config.organisatie_rsin,
                    "iot_submission_report": config.iot_submission_report,
                    "iot_submission_csv": config.iot_submission_csv,
                    "iot_attachment": config.iot_attachment,
                },
            )

    def validate_result(self, model: ObjectsAPIGroupConfigModel) -> None:
        names = [config.name for config in model.groups]
        failed_checks = []
        for config in ObjectsAPIGroupConfig.objects.filter(name__in=names):
            if config.catalogue_domain and config.catalogue_rsin:
                catalogi_client = get_catalogi_client(config)

                catalogus = None
                try:
                    catalogus = catalogi_client.find_catalogus(
                        domain=config.catalogue_domain, rsin=config.catalogue_rsin
                    )
                    if not catalogus:
                        raise ValueError(
                            f"No catalogus found for domain {config.catalogue_domain} and RSIN {config.catalogue_rsin}"
                        )
                except Exception as exc:
                    failed_checks.append(exc)

                if not catalogus:
                    continue

                fields = [
                    "iot_submission_report",
                    "iot_submission_csv",
                    "iot_attachment",
                ]
                for field in fields:
                    if description := getattr(config, field, None):
                        iotype = catalogi_client.find_informatieobjecttypen(
                            catalogus=catalogus["url"], description=description
                        )
                        try:
                            iotype = catalogi_client.find_informatieobjecttypen(
                                catalogus=catalogus["url"], description=description
                            )
                            if not iotype:
                                raise ValueError(
                                    f"No Informatieobjecttype found for catalogus {catalogus['url']} and description {description}"
                                )
                        except Exception as exc:
                            failed_checks.append(str(exc))

        if failed_checks:
            error_msgs = ""
            for msg in failed_checks:
                error_msgs += f"- {msg}\n"
            raise SelfTestFailed(
                f"The following issue(s) occurred while testing the configuration:\n{error_msgs}"
            )
