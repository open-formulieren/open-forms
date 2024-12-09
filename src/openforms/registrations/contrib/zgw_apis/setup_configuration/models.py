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

    # FIXME choices and blank=True doesn't seem to be picked up properly
    zaak_vertrouwelijkheidaanduiding: str = DjangoModelRef(
        ZGWApiGroupConfig,
        "zaak_vertrouwelijkheidaanduiding",
        default="",
    )
    doc_vertrouwelijkheidaanduiding: str = DjangoModelRef(
        ZGWApiGroupConfig, "doc_vertrouwelijkheidaanduiding", default=""
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
            ]
        }


class ZGWApiGroupConfigModel(ConfigurationModel):
    groups: list[SingleZGWApiGroupConfigModel] = Field(default_factory=list)
