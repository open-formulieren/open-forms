from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from pydantic import Field

from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig


class SingleZGWApiGroupConfigModel(ConfigurationModel):
    zaken_service_identifier: str = DjangoModelRef(ZGWApiGroupConfig, "zrc_service")
    documenten_service_identifier: str = DjangoModelRef(
        ZGWApiGroupConfig,
        "drc_service",
    )
    catalogi_service_identifier: str = DjangoModelRef(
        ZGWApiGroupConfig,
        "ztc_service",
    )

    # Slightly more descriptive name
    objects_api_json_content_template: str = DjangoModelRef(
        ZGWApiGroupConfig, "content_json"
    )

    class Meta:
        django_model_refs = {
            ZGWApiGroupConfig: [
                "name",
                "identifier",
                "catalogue_domain",
                "catalogue_rsin",
                "organisatie_rsin",
                "auteur",
                "zaak_vertrouwelijkheidaanduiding",
                "doc_vertrouwelijkheidaanduiding",
            ]
        }
        extra_kwargs = {
            "identifier": {"examples": ["open-zaak-acceptance"]},
            "name": {"examples": ["Open Zaak acceptance environment"]},
            "catalogue_domain": {"examples": ["ABCD"]},
            "catalogue_rsin": {"examples": ["111222333"]},
            "organisatie_rsin": {"examples": ["123456782"]},
        }


class ZGWApiGroupConfigModel(ConfigurationModel):
    groups: list[SingleZGWApiGroupConfigModel] = Field()
