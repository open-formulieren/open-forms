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

    class Meta:
        django_model_refs = {
            ObjectsAPIGroupConfig: [
                "name",
                "identifier",
                "organisatie_rsin",
            ]
        }
        extra_kwargs = {
            "identifier": {"examples": ["objects-api-acceptance"]},
            "name": {"examples": ["Objecten acceptance environment"]},
            "organisatie_rsin": {"examples": ["123456782"]},
        }


class ObjectsAPIGroupConfigModel(ConfigurationModel):
    groups: list[SingleObjectsAPIGroupConfigModel] = Field()
