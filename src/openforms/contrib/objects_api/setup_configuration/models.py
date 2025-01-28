from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import Field

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig


class SingleObjectsAPIGroupConfigModel(ConfigurationModel):
    objects_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "objects_service", examples=["objects-api"]
    )
    objecttypes_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "objecttypes_service", examples=["objecttypes-api"]
    )
    documenten_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "drc_service", default="", examples=["documenten-api"]
    )
    catalogi_service_identifier: str = DjangoModelRef(
        ObjectsAPIGroupConfig, "catalogi_service", default="", examples=["catalogi-api"]
    )

    # Renamed to be more descriptive
    document_type_submission_report: str = DjangoModelRef(
        ObjectsAPIGroupConfig,
        "iot_submission_report",
        examples=["PDF Informatieobjecttype"],
    )
    document_type_submission_csv: str = DjangoModelRef(
        ObjectsAPIGroupConfig,
        "iot_submission_csv",
        examples=["CSV Informatieobjecttype"],
    )
    document_type_attachment: str = DjangoModelRef(
        ObjectsAPIGroupConfig,
        "iot_attachment",
        examples=["Attachment Informatieobjecttype"],
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
        extra_kwargs = {
            "identifier": {"examples": ["objects-api-acceptance"]},
            "name": {"examples": ["Objecten acceptance environment"]},
            "catalogue_domain": {"examples": ["ABCD"]},
            "catalogue_rsin": {"examples": ["111222333"]},
            "organisatie_rsin": {"examples": ["123456782"]},
        }


class ObjectsAPIGroupConfigModel(ConfigurationModel):
    groups: list[SingleObjectsAPIGroupConfigModel] = Field()
