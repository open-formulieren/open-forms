from typing import Any

from django.db.models import IntegerChoices, Q
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin

from .client import get_catalogi_client, get_objecttypes_client
from .models import ObjectsAPIGroupConfig


class VersionChoices(IntegerChoices):
    V1 = 1, _("v1, template based")
    V2 = 2, _("v2, variables mapping")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Variable mapping example",
            value={
                "variable_key": "a_component_variable",
                "target_path": ["path", "to.the", "target"],
            },
        )
    ]
)
class ObjecttypeVariableMappingSerializer(serializers.Serializer):
    """A mapping between a form variable key and the corresponding Objecttype JSON location."""

    variable_key = FormioVariableKeyField(
        label=_("variable key"),
        help_text=_(
            "The 'dotted' path to a form variable key. The format should comply to how Formio handles nested component keys."
        ),
    )
    target_path = serializers.ListField(
        child=serializers.CharField(label=_("Segment of a JSON path")),
        label=_("target path"),
        help_text=_(
            "Representation of the JSON target location as a list of string segments."
        ),
    )


class ObjectsAPIOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    objects_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.exclude(
            Q(objects_service=None)
            | Q(objecttypes_service=None)
            | Q(drc_service=None)
            | Q(catalogi_service=None)
        ),
        label=("Objects API group"),
        help_text=_("Which Objects API group to use."),
    )
    version = serializers.ChoiceField(
        label=_("options version"),
        help_text=_(
            "The schema version of the objects API Options. Not to be confused with the objecttype version."
        ),
        choices=VersionChoices.choices,
        default=1,
    )
    objecttype = serializers.URLField(
        label=_("objecttype"),
        help_text=_(
            "URL that points to the ProductAanvraag objecttype in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
    )
    objecttype_version = serializers.IntegerField(
        label=_("objecttype version"),
        help_text=_("Version of the objecttype in the Objecttypes API"),
    )
    informatieobjecttype_submission_report = serializers.URLField(
        label=_("submission report PDF informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report PDF"
        ),
        required=False,
    )
    upload_submission_csv = serializers.BooleanField(
        label=_("Upload submission CSV"),
        help_text=_(
            "Indicates whether or not the submission CSV should be uploaded as "
            "a Document in Documenten API and attached to the ProductAanvraag"
        ),
        default=False,
    )
    informatieobjecttype_submission_csv = serializers.URLField(
        label=_("submission report CSV informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report CSV"
        ),
        required=False,
    )
    informatieobjecttype_attachment = serializers.URLField(
        label=_("attachment informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission attachments"
        ),
        required=False,
    )
    organisatie_rsin = serializers.CharField(
        label=_("organisation RSIN"),
        validators=[validate_rsin],
        help_text=_("RSIN of organization, which creates the INFORMATIEOBJECT"),
        required=False,
    )

    # V1 only fields:
    productaanvraag_type = serializers.CharField(
        label=_("productaanvraag type"),
        help_text=_("The type of ProductAanvraag"),
        required=False,
    )
    content_json = serializers.CharField(
        label=_("JSON content field"),
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
    payment_status_update_json = serializers.CharField(
        label=_("payment status update JSON template"),
        help_text=_(
            "This template is evaluated with the submission data and the resulting JSON is sent to the objects API "
            "with a PATCH to update the payment field."
        ),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        required=False,
    )

    # V2 only fields:
    variables_mapping = ObjecttypeVariableMappingSerializer(
        label=_("variables mapping"),
        many=True,
        required=False,
    )

    # As `record.geometry` is outside `record.data`, we special case this attribute:
    geometry_variable_key = FormioVariableKeyField(
        label=_("geometry variable"),
        help_text=_(
            "The 'dotted' path to a form variable key that should be mapped to the `record.geometry` attribute."
        ),
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        v1_only_fields = {
            "productaanvraag_type",
            "content_json",
            "payment_status_update_json",
        }
        v2_only_fields = {"variables_mapping", "geometry_variable_key"}

        version = get_from_serializer_data_or_instance("version", attrs, self)

        match version:
            case VersionChoices.V1:
                v1_forbidden_fields = v2_only_fields.intersection(attrs)
                if v1_forbidden_fields:
                    raise ValidationError(
                        {
                            k: _(
                                "{field_name} shouldn't be provided when version is 1"
                            ).format(field_name=k)
                            for k in v1_forbidden_fields
                        }
                    )
            case VersionChoices.V2:
                v2_forbidden_fields = v1_only_fields.intersection(attrs)
                if v2_forbidden_fields:
                    raise ValidationError(
                        {
                            k: _(
                                "{field_name} shouldn't be provided when version is 2"
                            ).format(field_name=k)
                            for k in v2_forbidden_fields
                        }
                    )
            case _:  # pragma: no cover
                raise ValidationError(
                    {"version": _("Unknown version: {version}").format(version=version)}
                )

        if not self.context.get("validate_business_logic", True):
            return attrs

        objects_api_group: ObjectsAPIGroupConfig = attrs["objects_api_group"]
        with get_catalogi_client(objects_api_group) as catalogi_client:
            informatieobjecttypen = catalogi_client.get_all_informatieobjecttypen()

        for field in (
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        ):
            url = attrs.get(field)
            if url is not None and not any(
                informatieobjecttype["url"] == url
                for informatieobjecttype in informatieobjecttypen
            ):
                raise serializers.ValidationError(
                    {
                        field: _(
                            "The provided {field} does not exist in the Catalogi API."
                        ).format(field=field)
                    },
                    code="not-found",
                )

        with get_objecttypes_client(objects_api_group) as objecttypes_client:
            objecttypes = objecttypes_client.list_objecttypes()

            matching_objecttype = next(
                (
                    objecttype
                    for objecttype in objecttypes
                    if objecttype["url"] == attrs["objecttype"]
                ),
                None,
            )

            if matching_objecttype is None:
                raise serializers.ValidationError(
                    {
                        "objecttype": _(
                            "The provided objecttype does not exist in the Objecttypes API."
                        )
                    },
                    code="not-found",
                )

            objecttype_versions = objecttypes_client.list_objecttype_versions(
                objecttype_uuid=matching_objecttype["uuid"]
            )

            if not any(
                objecttype_version["version"] == attrs["objecttype_version"]
                for objecttype_version in objecttype_versions
            ):
                raise serializers.ValidationError(
                    {
                        "objecttype_version": _(
                            "The provided objecttype version does not exist in the Objecttypes API."
                        )
                    },
                    code="not-found",
                )

        return attrs
