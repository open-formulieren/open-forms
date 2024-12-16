import warnings
from uuid import UUID

from django.db.models import IntegerChoices, Q
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from furl import furl
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.contrib.objects_api.clients import (
    get_catalogi_client,
    get_objecttypes_client,
)
from openforms.contrib.zgw.serializers import CatalogueSerializer
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin

from .models import ObjectsAPIGroupConfig
from .typing import RegistrationOptions


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
    catalogue = CatalogueSerializer(
        label=_("catalogue"),
        required=False,
        help_text=_(
            "The catalogue in the catalogi API from the selected API group. This "
            "overrides the catalogue specified in the API group, if it's set. When "
            "specified, the document types specified on the API group are ignored."
        ),
    )
    version = serializers.ChoiceField(
        label=_("options version"),
        help_text=_(
            "The schema version of the objects API Options. Not to be confused with the objecttype version."
        ),
        choices=VersionChoices.choices,
        default=1,
    )
    objecttype = serializers.UUIDField(
        label=_("objecttype"),
        help_text=_(
            "UUID of the ProductAanvraag objecttype in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
    )
    objecttype_version = serializers.IntegerField(
        label=_("objecttype version"),
        help_text=_("Version of the objecttype in the Objecttypes API."),
    )
    update_existing_object = serializers.BooleanField(
        label=_("Update existing object"),
        help_text=_(
            "Indicates whether the existing object should be updated (if it exists), instead of creating a new one."
        ),
        default=False,
    )
    upload_submission_csv = serializers.BooleanField(
        label=_("Upload submission CSV"),
        help_text=_(
            "Indicates whether or not the submission CSV should be uploaded as "
            "a Document in Documenten API and attached to the ProductAanvraag."
        ),
        default=False,
    )
    organisatie_rsin = serializers.CharField(
        label=_("organisation RSIN"),
        validators=[validate_rsin],
        help_text=_("RSIN of organization, which creates the INFORMATIEOBJECT."),
        required=False,
    )

    iot_submission_report = serializers.CharField(
        label=_("submission report document type description"),
        required=False,
        allow_blank=True,
        max_length=80,
        default="",
        help_text=_(
            "Description of the document type in the Catalogi API to be used for the "
            "submission report PDF. The appropriate version will automatically be "
            "selected based on the submission timestamp and validity dates of the "
            "document type versions."
        ),
    )
    iot_submission_csv = serializers.CharField(
        label=_("submission report CSV document type description"),
        required=False,
        allow_blank=True,
        max_length=80,
        default="",
        help_text=_(
            "Description of the document type in the Catalogi API to be used for the "
            "submission report CSV. The appropriate version will automatically be "
            "selected based on the submission timestamp and validity dates of the "
            "document type versions."
        ),
    )
    iot_attachment = serializers.CharField(
        label=_("attachment document type description"),
        required=False,
        allow_blank=True,
        max_length=80,
        default="",
        help_text=_(
            "Description of the document type in the Catalogi API to be used for the "
            "submission attachments. The appropriate version will automatically be "
            "selected based on the submission timestamp and validity dates of the "
            "document type versions."
        ),
    )

    # DeprecationWarning: remove in OF 3.0
    informatieobjecttype_submission_report = serializers.URLField(
        label=_("submission report PDF informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report PDF."
        ),
        required=False,
        allow_blank=True,
    )
    informatieobjecttype_submission_csv = serializers.URLField(
        label=_("submission report CSV informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report CSV."
        ),
        required=False,
        allow_blank=True,
    )
    informatieobjecttype_attachment = serializers.URLField(
        label=_("attachment informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission attachments."
        ),
        required=False,
        allow_blank=True,
    )

    # V1 only fields:
    productaanvraag_type = serializers.CharField(
        label=_("productaanvraag type"),
        help_text=_("The type of ProductAanvraag."),
        required=False,
        allow_blank=True,
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
        allow_blank=True,
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
        allow_blank=True,
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

    def get_fields(self):
        fields = super().get_fields()
        if getattr(self, "swagger_fake_view", False) or not self.context.get(
            "is_import", False
        ):
            return fields

        # If in an import context, we don't want to error on missing groups.
        # Instead, we will try to set one if possible in the `validate` method.
        # We also change the `objecttype` field to be any string, as it could be an URL.
        fields["objects_api_group"].required = False
        fields["objecttype"] = serializers.CharField()
        return fields

    # XXX: fix typehint of attrs, it's a wider version of RegistrationOptions where
    # the UUID is still a string...
    def _handle_import(self, attrs) -> None:
        if (
            self.context.get("is_import", False)
            and attrs.get("objects_api_group") is None
        ):
            existing_groups = (
                ObjectsAPIGroupConfig.objects.order_by("pk")
                .exclude(
                    Q(objects_service=None)
                    | Q(objecttypes_service=None)
                    | Q(drc_service=None)
                    | Q(catalogi_service=None)
                )
                .all()
            )

            if not existing_groups.exists():
                raise serializers.ValidationError(
                    {
                        "objects_api_group": _(
                            "You must create a valid Objects API Group config (with the necessary services) before importing."
                        )
                    }
                )

            # As `objects_api_group` isn't in `attrs`, the objecttype is guaranteed to be an URL
            # as Objects API groups were added before objecttypes were changed from URL to UUID.
            # (the conversion is done at the end of this function).
            matching_group = next(
                (
                    group
                    for group in existing_groups
                    if attrs["objecttype"].startswith(
                        group.objecttypes_service.api_root
                    )
                ),
                None,
            )

            if matching_group is None:
                raise serializers.ValidationError(
                    {
                        "objects_api_group": _(
                            "No Objects API Group config was found matching the configured objecttype URL."
                        )
                    }
                )

            attrs["objects_api_group"] = matching_group

        try:
            attrs["objecttype"] = UUID(str(attrs["objecttype"]).rsplit("/", 1)[1])
        except IndexError:
            pass

    def validate(self, attrs: RegistrationOptions) -> RegistrationOptions:
        self._handle_import(attrs)

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
                    raise serializers.ValidationError(
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
                    raise serializers.ValidationError(
                        {
                            k: _(
                                "{field_name} shouldn't be provided when version is 2"
                            ).format(field_name=k)
                            for k in v2_forbidden_fields
                        }
                    )
            case _:  # pragma: no cover
                raise serializers.ValidationError(
                    {"version": _("Unknown version: {version}").format(version=version)}
                )

        if not self.context.get("validate_business_logic", True):
            return attrs

        _validate_catalogue_and_document_types(attrs)
        _validate_objecttype_and_version(attrs)

        return attrs


def _validate_catalogue_and_document_types(attrs: RegistrationOptions) -> None:
    """
    Validate that the catalogue and document types exist.

    Document type validation is layered - serializer options overrule API group fields.
    Some notable cases to consider:

    - No serializer catalogue is specified: any document type fields are validated
      against the API group catalogue.
    - A serializer catalogue is specified: only document type fields from the serializer
      are considered, and they are validated against the serializer catalogue. Any
      defaults specified on the API group are ignored. This implies that document type
      fields not specified on the serializer that are set on the API group will NOT
      result in uploads.

    Doing something else would require us to "hoist" configuration from the API group
    to the serializer and that doesn't seem logical.
    """
    api_group = attrs["objects_api_group"]
    catalogus = None
    catalogue_option = attrs.get("catalogue")

    domain, rsin = (
        (
            catalogue_option["domain"],
            catalogue_option["rsin"],
        )
        if catalogue_option is not None
        else (
            api_group.catalogue_domain,
            api_group.catalogue_rsin,
        )
    )

    # validate the catalogue itself - the queryset in the field guarantees that
    # api_group.catalogi_service is not null.
    with get_catalogi_client(api_group) as client:
        # DB check constraint + serializer validation guarantee that both or none
        # are empty at the same time
        if domain and rsin:
            catalogus = client.find_catalogus(domain=domain, rsin=rsin)
            if catalogus is None:
                raise serializers.ValidationError(
                    {
                        "catalogue": _(
                            "The specified catalogue does not exist. Maybe you made a "
                            "typo in the domain or RSIN?"
                        ),
                    },
                    code="invalid-catalogue",
                )

            informatieobjecttypen_urls = catalogus["informatieobjecttypen"]
        else:
            # Previously all informatieobjecttypen were fetched here, if there were no
            # catalogue domain and RSIN specified and the legacy fields were used.
            # This led to bad performance if the Catalogi service has a lot of IOtypen however
            # So instead we validate each URL separately by checking if the prefix of the
            # URL matches and if we can retrieve it (see below)
            # issue: https://github.com/open-formulieren/open-forms/issues/4695
            informatieobjecttypen_urls = None

        _errors = {}
        for field in (
            "iot_submission_report",
            "iot_submission_csv",
            "iot_attachment",
        ):
            if not (description := attrs[field]):
                continue
            # catalogue must be specified if making use of the reference-by-description
            # config options.
            if catalogus is None:
                err_msg = _(
                    "To look up document types by their description, a catalogue reference "
                    "is required. Either specify one on the API group or in the plugin "
                    "options."
                )
                raise serializers.ValidationError(
                    {"catalogue": err_msg}, code="required"
                )

            versions = client.find_informatieobjecttypen(
                catalogus=catalogus["url"], description=description
            )
            if versions is None:
                err_msg = _(
                    "No document type with description '{description}' found."
                ).format(description=description)
                _errors[field] = ErrorDetail(err_msg, code="not-found")
        if _errors:
            raise serializers.ValidationError(_errors)

        # Remove these legacy fields in Open Forms 3.0
        for field in (
            "informatieobjecttype_submission_report",
            "informatieobjecttype_submission_csv",
            "informatieobjecttype_attachment",
        ):
            url = attrs.get(field)
            if not url:
                continue

            warnings.warn(
                "URL references to document types are deprecated and will be remove in "
                "Open Forms 3.0",
                DeprecationWarning,
            )

            err_tpl = (
                _("The provided {field} does not exist in the Catalogi API.")
                if catalogus is None
                else _("The provided {field} does not exist in the selected catalogue.")
            )
            err_msg = err_tpl.format(field=field)

            if informatieobjecttypen_urls is not None:
                if url not in informatieobjecttypen_urls:
                    raise serializers.ValidationError(
                        {field: err_msg}, code="not-found"
                    )
            else:
                assert api_group.catalogi_service
                iotypen_endpoint = (
                    furl(api_group.catalogi_service.api_root) / "informatieobjecttypen/"
                ).url

                if not url.startswith(iotypen_endpoint):
                    raise serializers.ValidationError(
                        {field: err_msg}, code="not-found"
                    )

                response = (
                    client.head(url)
                    if client.api_version >= (1, 1, 0)
                    else client.get(url)
                )

                if response.status_code != 200:
                    raise serializers.ValidationError(
                        {field: err_msg}, code="not-found"
                    )


def _validate_objecttype_and_version(attrs: RegistrationOptions) -> None:
    with get_objecttypes_client(attrs["objects_api_group"]) as objecttypes_client:
        objecttypes = objecttypes_client.list_objecttypes()

        matching_objecttype = next(
            (
                objecttype
                for objecttype in objecttypes
                if objecttype["uuid"] == str(attrs["objecttype"])
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
