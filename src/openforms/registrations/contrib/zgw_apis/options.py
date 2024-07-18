from typing import Any

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.contrib.zgw.clients.catalogi import omschrijving_matcher
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin

from .client import get_catalogi_client
from .models import ZGWApiGroupConfig


class MappedVariablePropertySerializer(serializers.Serializer):
    component_key = FormioVariableKeyField(
        label=_("Component key"),
        help_text=_("Key of the form variable to take the value from."),
    )
    eigenschap = serializers.CharField(
        label=_("Property"),
        max_length=20,
        help_text=_(
            "Name of the property on the case type to which the variable will be "
            "mapped."
        ),
    )


class ZaakOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.exclude(
            Q(zrc_service=None) | Q(drc_service=None) | Q(ztc_service=None)
        ),
        help_text=_("Which ZGW API set to use."),
        label=_("ZGW API set"),
    )
    zaaktype = serializers.URLField(
        required=True, help_text=_("URL of the ZAAKTYPE in the Catalogi API")
    )
    informatieobjecttype = serializers.URLField(
        required=True,
        help_text=_("URL of the INFORMATIEOBJECTTYPE in the Catalogi API"),
    )
    organisatie_rsin = serializers.CharField(
        required=False,
        validators=[validate_rsin],
        help_text=_("RSIN of organization, which creates the ZAAK"),
    )
    zaak_vertrouwelijkheidaanduiding = serializers.ChoiceField(
        label=_("Vertrouwelijkheidaanduiding"),
        required=False,
        choices=VertrouwelijkheidsAanduidingen.choices,
        help_text=_(
            "Indication of the level to which extend the dossier of the ZAAK is meant to be public."
        ),
    )
    medewerker_roltype = serializers.CharField(
        required=False,
        help_text=_(
            "Description (omschrijving) of the ROLTYPE to use for employees filling in a form for a citizen/company."
        ),
    )

    # Objects API
    objecttype = serializers.URLField(
        label=_("objects API - objecttype"),
        help_text=_(
            "URL that points to the ProductAanvraag objecttype in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
        required=False,
    )
    objecttype_version = serializers.IntegerField(
        label=_("objects API - objecttype version"),
        help_text=_("Version of the objecttype in the Objecttypes API"),
        required=False,
    )
    content_json = serializers.CharField(
        label=_("objects API - JSON content field"),
        help_text=_(
            "JSON template for the body of the request sent to the Objects API."
        ),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        required=False,
    )

    # Eigenschappen
    property_mappings = MappedVariablePropertySerializer(
        many=True,
        label=_("Variable-to-property mappings"),
        required=False,
    )

    def get_fields(self):
        fields = super().get_fields()
        if getattr(self, "swagger_fake_view", False) or not self.context.get(
            "is_import", False
        ):
            return fields

        # If in an import context, we don't want to error on missing groups.
        # Instead, we will try to set one if possible in the `validate` method.
        fields["zgw_api_group"].required = False
        return fields

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        validate_business_logic = self.context.get("validate_business_logic", True)
        if not validate_business_logic:
            return attrs

        if self.context.get("is_import", False) and attrs.get("zgw_api_group") is None:
            existing_group = (
                ZGWApiGroupConfig.objects.order_by("pk")
                .exclude(
                    Q(zrc_service=None) | Q(drc_service=None) | Q(ztc_service=None)
                )
                .first()
            )
            if existing_group is None:
                raise serializers.ValidationError(
                    {
                        "zgw_api_group": _(
                            "You must create a valid ZGW API Group config (with the necessary services) before importing."
                        )
                    }
                )
            else:
                attrs["zgw_api_group"] = existing_group

        group_config = attrs["zgw_api_group"]

        # Run all validations against catalogi API in the same connection pool.
        with get_catalogi_client(group_config) as client:
            catalogi = list(client.get_all_catalogi())

            # validate that the zaaktype is in the provided catalogi
            zaaktype_url = attrs["zaaktype"]
            zaaktype_exists = any(
                zaaktype_url in catalogus["zaaktypen"] for catalogus in catalogi
            )
            if not zaaktype_exists:
                raise serializers.ValidationError(
                    {
                        "zaaktype": _(
                            "The provided zaaktype does not exist in the specified "
                            "Catalogi API."
                        )
                    },
                    code="not-found",
                )

            # validate that the informatieobjecttype is in the provided catalogi
            informatieobjecttype_url = attrs["informatieobjecttype"]
            informatieobjecttype_exists = any(
                informatieobjecttype_url in catalogus["informatieobjecttypen"]
                for catalogus in catalogi
            )
            if not informatieobjecttype_exists:
                raise serializers.ValidationError(
                    {
                        "informatieobjecttype": _(
                            "The provided informatieobjecttype does not exist in the "
                            "specified Catalogi API."
                        )
                    },
                    code="not-found",
                )

            # Make sure the property (eigenschap) related to the zaaktype exists
            if mappings := attrs.get("property_mappings"):
                eigenschappen = client.list_eigenschappen(zaaktype=attrs["zaaktype"])
                retrieved_eigenschappen = {
                    eigenschap["naam"]: eigenschap["url"]
                    for eigenschap in eigenschappen
                }

                errors = []
                for mapping in mappings:
                    if mapping["eigenschap"] not in retrieved_eigenschappen:
                        errors.append(
                            _(
                                "Could not find a property with the name "
                                "'{property_name}' related to the zaaktype."
                            ).format(property_name=mapping["eigenschap"])
                        )

                if errors:
                    raise serializers.ValidationError(
                        {"property_mappings": errors}, code="invalid"
                    )

            if "medewerker_roltype" in attrs:
                roltypen = client.list_roltypen(
                    zaaktype=attrs["zaaktype"],
                    matcher=omschrijving_matcher(attrs["medewerker_roltype"]),
                )
                if not roltypen:
                    raise serializers.ValidationError(
                        {
                            "medewerker_roltype": _(
                                "Could not find a roltype with this description related to the zaaktype."
                            )
                        },
                        code="invalid",
                    )

        return attrs
