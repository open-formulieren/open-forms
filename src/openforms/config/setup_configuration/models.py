from django_setup_configuration.models import ConfigurationModel, DjangoModelRef
from pydantic import Field

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig


class SingleObjectsAPIGroupConfigModel(ConfigurationModel):
    objects_service_slug: str = DjangoModelRef(ObjectsAPIGroupConfig, "objects_service")
    objecttypes_service_slug: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "objecttypes_service"
    )
    drc_service_slug: str = DjangoModelRef(ObjectsAPIGroupConfig, "drc_service")
    catalogi_service_slug: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "catalogi_service"
    )

    class Meta:
        django_model_refs = {
            ObjectsAPIGroupConfig: [
                "name",
                "catalogue_domain",
                "catalogue_rsin",
                "organisatie_rsin",
                "iot_submission_report",
                "iot_submission_csv",
                "iot_attachment",
            ]
        }


class ObjectsAPIGroupConfigModel(ConfigurationModel):
    groups: list[SingleObjectsAPIGroupConfigModel] = Field(default_factory=list)
