from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import Field

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig


class SingleObjectsAPIGroupConfigModel(ConfigurationModel):
    objects_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "objects_service"
    )
    objecttypes_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "objecttypes_service"
    )
    documenten_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "drc_service", default=""
    )
    catalogi_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "catalogi_service", default=""
    )

    # Renamed to be more descriptive
    document_type_submission_report: str = DjangoModelRef(
        ObjectsAPIGroupConfig,
        "iot_submission_report",
    )
    document_type_submission_csv: str = DjangoModelRef(
        ObjectsAPIGroupConfig,
        "iot_submission_csv",
    )
    document_type_attachment: str = DjangoModelRef(
        ObjectsAPIGroupConfig,
        "iot_attachment",
    )

    class Meta:
        django_model_refs = {
            ObjectsAPIGroupConfig: [
                "name",
                "identifier",
                "catalogue_domain",
                "catalogue_rsin",
                "organisatie_rsin",
            ]
        }


class ObjectsAPIGroupConfigModel(ConfigurationModel):
    groups: list[SingleObjectsAPIGroupConfigModel] = Field(default_factory=list)
