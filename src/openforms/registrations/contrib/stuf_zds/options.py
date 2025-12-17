from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin
from stuf.stuf_zds.constants import VertrouwelijkheidsAanduidingen

from .typing import MappingItem


def default_variables_mapping() -> list[MappingItem]:
    return [
        {
            "form_variable": "payment_completed",
            "stuf_name": "payment_completed",
        },
        {
            "form_variable": "payment_amount",
            "stuf_name": "payment_amount",
        },
        {
            "form_variable": "payment_public_order_ids",
            "stuf_name": "payment_public_order_ids",
        },
        {
            "form_variable": "provider_payment_ids",
            "stuf_name": "provider_payment_ids",
        },
    ]


class MappingSerializer(serializers.Serializer):
    form_variable = serializers.CharField(
        help_text=_("The name of the form variable to be mapped")
    )
    stuf_name = serializers.CharField(
        help_text=_("The name in StUF-ZDS to which the form variable should be mapped"),
        label=_("StUF-ZDS name"),
    )


class ZaakOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    zds_zaaktype_code = serializers.CharField(
        required=True,
        help_text=_("Zaaktype code for newly created Zaken in StUF-ZDS"),
    )
    zds_zaaktype_omschrijving = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Zaaktype description for newly created Zaken in StUF-ZDS"),
    )

    zds_zaaktype_status_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Zaaktype status code for newly created zaken in StUF-ZDS"),
    )
    zds_zaaktype_status_omschrijving = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_("Zaaktype status omschrijving for newly created zaken in StUF-ZDS"),
    )

    zds_documenttype_omschrijving_inzending = serializers.CharField(
        required=True,
        allow_blank=True,
        help_text=_("Documenttype description for newly created zaken in StUF-ZDS"),
    )

    zds_zaakdoc_vertrouwelijkheid = serializers.ChoiceField(
        label=_("Document confidentiality level"),
        choices=VertrouwelijkheidsAanduidingen.choices,
        # older versions from before this version was added do not have this field in
        # the saved data. In those cases, the default is used.
        default=VertrouwelijkheidsAanduidingen.vertrouwelijk,
        help_text=_(
            "Indication of the level to which extend the dossier of the ZAAK is meant "
            "to be public. This is set on the documents created for the ZAAK."
        ),
    )

    variables_mapping = MappingSerializer(
        many=True,
        label=_("Variables mapping"),
        help_text=_(
            "This mapping is used to map the variable keys to keys used in the XML "
            "that is sent to StUF-ZDS. Those keys and the values belonging to them in "
            "the submission data are included in extraElementen."
        ),
        required=False,
    )

    @classmethod
    def display_as_jsonschema(cls):
        data = super().display_as_jsonschema()
        # Workaround because drf_jsonschema_serializer does not pick up defaults
        data["properties"]["variables_mapping"]["default"] = default_variables_mapping()
        # To avoid duplicating the title and help text for each item
        del data["properties"]["variables_mapping"]["items"]["title"]
        del data["properties"]["variables_mapping"]["items"]["description"]
        return data

    def _handle_import(self, attrs) -> None:
        # we're not importing, nothing to do
        if not self.context.get("is_import", False) or not hasattr(
            self, "initial_data"
        ):
            return

        # needed for StUF-ZDS backwards compatibility (see issue #5776)
        if (
            self.initial_data
            and isinstance(self.initial_data, dict)
            and "payment_status_update_mapping" in self.initial_data
        ):
            attrs["variables_mapping"] = self.initial_data.pop(
                "payment_status_update_mapping"
            )

    def validate(self, attrs):
        self._handle_import(attrs)
        return super().validate(attrs)
