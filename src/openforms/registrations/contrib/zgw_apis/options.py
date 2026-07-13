from collections.abc import Iterator
from functools import partial
from typing import Protocol, TypedDict

from django.db.models import Q
from django.utils.translation import gettext, gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.api.fields import (
    PrimaryKeyRelatedAsChoicesField,
    SlugRelatedAsChoicesField,
)
from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.zgw.clients.catalogi import (
    CaseType,
    CatalogiClient,
    Catalogus,
    omschrijving_matcher,
)
from openforms.contrib.zgw.serializers import CatalogueSerializer
from openforms.formio.api.fields import FormioVariableKeyField
from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin

from .client import get_catalogi_client
from .constants import CaseObjectTypeChoices, SummaryDocumentChoices
from .models import ZGWApiGroupConfig
from .typing import RegistrationOptions


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


class JSONMultipleChoiceField(serializers.MultipleChoiceField):
    def to_representation(self, value) -> list[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        # Return a list as MultipleChoiceField fields return a set here by default
        # which cannot be serialized to JSON with python's stdlib JSON encoder.
        return list(super().to_representation(value))


class FileComponentOptionsSerializer(serializers.Serializer):
    key = FormioVariableKeyField(
        label=_("component key"),
        help_text=_(
            "Literal component key value of the file component for which the options "
            "apply."
        ),
    )
    document_type_description = serializers.CharField(
        label=_("Document type description"),
        required=False,
        help_text=_(
            "The document type will be retrieved from the catalogue and case type "
            "specified in the backend options. The version will automatically be "
            "selected based on the submission completion timestamp. Only document "
            "types related to the case type are valid."
        ),
        allow_blank=True,
    )
    organization_rsin = serializers.CharField(
        validators=[validate_rsin],
        required=False,
        help_text=_("RSIN of the organization that creates the document."),
        allow_blank=True,
    )
    confidentiality_level = serializers.ChoiceField(
        label=_("Vertrouwelijkheidaanduiding"),
        required=False,
        choices=VertrouwelijkheidsAanduidingen.choices,
        help_text=_(
            "Indication of the level to which extend the document is meant to be "
            "public."
        ),
        allow_blank=True,
    )
    title = serializers.CharField(
        label=_("Title"),
        required=False,
        help_text=_(
            "Optional custom title for the document. By default, the attachment file "
            "name is used."
        ),
        allow_blank=True,
    )


class ObjectOverigeSerializer(serializers.Serializer):
    overige_data = serializers.CharField(
        label=_("Overige data"),
        help_text=_(
            "Data for the 'overige' object in a free format. You can use form variables here."
        ),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend")
        ],
    )


class CaseObjectSerializer(serializers.Serializer):
    # in the future this field can be turned to Discriminator for PolymorphicSerializer
    # but for now it will over-complicate things without benefits, so let's do KISS
    case_object_type = serializers.ChoiceField(
        label=_("Case object type"),
        choices=CaseObjectTypeChoices.choices,
        help_text=_("Type of the case object. Now only 'overige' value is supported."),
    )
    case_object_type_overige = serializers.CharField(
        label=_("Case object type overige"),
        max_length=100,
        allow_blank=True,
        help_text=_("Description of the 'overige' case object type."),
    )
    case_object_identification = ObjectOverigeSerializer(
        label=_("Case object identification"),
        help_text=_(
            "Data, which describes the object. The shape depends on the 'case_object_type'. "
            "Now only 'overige' data shape is supported."
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
    catalogue = CatalogueSerializer(
        label=_("catalogue"),
        required=True,
        help_text=_(
            "The catalogue in the catalogi API from the selected API group. This "
            "overrides the catalogue specified in the API group, if it's set. Case "
            "and document types specified will be resolved against this catalogue."
        ),
    )
    case_type_identification = serializers.CharField(
        required=True,
        label=_("Case type identification"),
        help_text=_(
            "The case type will be retrieved in the specified catalogue. The version "
            "will automatically be selected based on the submission completion "
            "timestamp. When you specify this field, you MUST also specify a catalogue."
        ),
        allow_blank=False,
    )
    document_type_description = serializers.CharField(
        required=True,
        label=_("Document type description"),
        help_text=_(
            "The document type will be retrieved in the specified catalogue. The version "
            "will automatically be selected based on the submission completion "
            "timestamp. When you specify this field, you MUST also specify the case "
            "type via its identification. Only document types related to the case type "
            "are valid."
        ),
        allow_blank=False,
    )
    product_url = serializers.URLField(
        label=_("Product url"),
        help_text=_(
            "The product url will be retrieved from the specified case type "
            "and the version that is active at that moment. "
        ),
        required=False,
        allow_blank=True,
        default="",
    )
    summary_documents = JSONMultipleChoiceField(
        choices=SummaryDocumentChoices.choices,
        label=_("Summary documents"),
        help_text=_("Which summary documents to include during registration."),
        default={SummaryDocumentChoices.pdf},
    )
    organisatie_rsin = serializers.CharField(
        required=False,
        validators=[validate_rsin],
        help_text=_("RSIN of organization, which creates the ZAAK"),
        allow_blank=True,
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
        allow_blank=True,
    )
    partners_roltype = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text=_(
            "Description (omschrijving) of the ROLTYPE to use for citizens filling in a form with partners."
        ),
    )
    partners_description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text=_(
            "Description (omschrijving) that will be used in the partners registration."
        ),
    )
    children_roltype = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text=_(
            "Description (omschrijving) of the ROLTYPE to use for citizens filling in a form with children."
        ),
    )
    children_description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text=_(
            "Description (omschrijving) that will be used in the children registration."
        ),
    )
    zaak_omschrijving = serializers.CharField(
        label=_("Omschrijving"),
        required=False,
        allow_blank=True,
        help_text=_(
            "Description (omschrijving) of the case. You can use the expressions like "
            "'{{ form_name }}' or other variables here. The resolved string is limited to 80 chars. "
            "If empty, the form name is used."
        ),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend")
        ],
    )
    zaak_toelichting = serializers.CharField(
        label=_("Toelichting"),
        required=False,
        allow_blank=True,
        help_text=_(
            "Explanation (toelichting) of the case. You can use the expressions like "
            "'{{ form_name }}' or other variables here."
        ),
        validators=[
            DjangoTemplateValidator(backend="openforms.template.openforms_backend")
        ],
    )

    # Objects API
    objects_api_group = SlugRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.exclude(
            Q(objects_service=None) | Q(objecttypes_service=None)
        ),
        slug_field="identifier",
        help_text=_("Which Objects API set to use."),
        label=_("Objects API set"),
        allow_null=True,
        default=None,
    )
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
        allow_blank=True,
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
        allow_blank=True,
    )

    # Eigenschappen
    property_mappings = MappedVariablePropertySerializer(
        many=True,
        label=_("Variable-to-property mappings"),
        required=False,
    )

    # File component options
    files = FileComponentOptionsSerializer(
        many=True,
        label=_("Files"),
        required=False,
        help_text=_(
            "List of file upload options for file components. Each entry contains the "
            "key of the file component in the form, which may be a child in an edit "
            "grid. Any specified option overrides the equivalent option on the backend "
            "level. If unspecified, the backend configuration is used."
        ),
        allow_null=False,
    )
    # Zaakobjecten
    case_objects = CaseObjectSerializer(
        many=True,
        label=_("Case Objects"),
        required=False,
        help_text=_("List of case objects."),
    )

    def _handle_import(self, attrs) -> None:
        # we're not importing, nothing to do
        if not self.context.get("is_import", False):
            return

        # it's already present in some form, nothing to do
        if "objects_api_group" in self.initial_data:
            return

        # no objecttype specified, no need to set a group
        if not attrs.get("objecttype"):
            return

        # at this point we know there's no api group provided and there *is* an
        # objecttype specified -> add the default group mimicking the legacy behaviour

        default_group = ObjectsAPIGroupConfig.objects.order_by("pk").first()
        # can't start making up groups, unfortunately we can only let validation block
        # the import now :(
        if default_group is None:
            return

        # patch up the data and set the default group as explicit option. it could be
        # the wrong one, which will be caught by downstream configuration and the only
        # way to resolve this is by fixing the import file
        attrs["objects_api_group"] = default_group

    def validate(self, attrs: RegistrationOptions) -> RegistrationOptions:
        self._handle_import(attrs)

        validate_business_logic = self.context.get("validate_business_logic", True)
        if not validate_business_logic:
            return attrs

        _validate_against_catalogi_api(attrs)

        if attrs.get("objecttype"):
            _validate_against_objects_api_group(attrs)

        return attrs


class CaseTypeVersionsIterator(Protocol):
    def __call__(self) -> Iterator[CaseType]: ...


def _iter_case_type_versions(
    client: CatalogiClient, catalogue: Catalogus, case_type_identification: str
) -> Iterator[CaseType]:
    case_type_versions = client.find_case_types(
        catalogus=catalogue["url"],
        identification=case_type_identification,
    )
    assert case_type_versions is not None
    yield from case_type_versions


def _validate_against_catalogi_api(attrs: RegistrationOptions) -> None:
    """
    Validate the configuration options against the specified catalogi API.

    1. If provided, validate that the specified catalogue exists in the configured
       Catalogi API (ZTC).
    2. Validate that the case type and document type exist:

        1. If a catalogue is provided (either in the options or on the API group),
           check that they are contained inside the specified catalogue.
        2. Otherwise, apply the legacy behaviour and validate that both exist in the
           specified Catalogi API.

    3. Validate that the configured case properties ("eigenschappen") exist on the
       specified case type.
    4. Validate that the employee role type ("medewerkerroltype") and the partner role
       type ("partnersroltype") exist on the specified case type.
    """
    with get_catalogi_client(attrs["zgw_api_group"]) as client:
        # validate the catalogue itself - the queryset in the field guarantees that
        # api_group.ztc_service is not null.
        result = _validate_catalogue_case_and_doc_type(client, attrs)

        iter_case_type_versions = partial(
            _iter_case_type_versions,
            client,
            result["catalogue"],
            attrs["case_type_identification"],
        )

        _validate_case_type_properties(
            client, attrs, iter_case_type_versions=iter_case_type_versions
        )
        _validate_medewerker_and_family_members_roltype(
            client, attrs, iter_case_type_versions=iter_case_type_versions
        )


def _validate_against_objects_api_group(attrs: RegistrationOptions) -> None:
    """
    Validate the configuration options against the specified objects API group.

    1. An `objects_api_group` must be specified
    2. The specified `objecttype` must have the same base URL as the defined `objects_api_group.objecttypes_service`
    """
    assert "objecttype" in attrs

    objects_api_group = attrs["objects_api_group"]
    if objects_api_group is None:
        raise serializers.ValidationError(
            {
                "objects_api_group": _(
                    "Objects API group must be specified if an objecttype is specified."
                )
            },
            code="required",
        )

    # `objecttypes_service` is required on `ObjectsAPIGroup`
    assert objects_api_group.objecttypes_service
    if not attrs["objecttype"].startswith(
        objects_api_group.objecttypes_service.api_root
    ):
        raise serializers.ValidationError(
            {
                "objecttype": _(
                    "The specified objecttype is not present in the selected "
                    "Objecttypes API (the URL does not start with the API root of "
                    "the Objecttypes API)."
                )
            },
            code="invalid",
        )


class _CatalogueAndTypeValidationResult(TypedDict):
    catalogue: Catalogus


def _validate_catalogue_case_and_doc_type(
    client: CatalogiClient, attrs: RegistrationOptions
) -> _CatalogueAndTypeValidationResult:
    _errors = {}

    catalogus = None
    catalogue_option = attrs["catalogue"]

    domain, rsin = catalogue_option["domain"], catalogue_option["rsin"]
    # serializer validation guarantees that both `domain` and `rsin` or none of them
    # are empty at the same time
    if not (domain and rsin):
        raise serializers.ValidationError(
            {
                "catalogue": _(
                    "You must specify a catalogue (got empty domain and RSIN)."
                )
            },
            code="required",
        )

    case_type_identification = attrs["case_type_identification"]
    document_type_description = attrs["document_type_description"]

    err_invalid_case_type = ErrorDetail(
        gettext("The provided zaaktype does not exist in the specified Catalogi API."),
        code="not-found",
    )
    err_invalid_document_type = ErrorDetail(
        gettext(
            "The provided informatieobjecttype does not exist in the selected case "
            "type or Catalogi API."
        ),
        code="not-found",
    )

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

    valid_document_type_urls = catalogus["informatieobjecttypen"]

    # serializer validation prevents blank case type identifications from being
    # configured.
    assert case_type_identification, "Case type identification may not be empty."
    case_type_versions = client.find_case_types(
        catalogus=catalogus["url"],
        identification=case_type_identification,
    )
    if case_type_versions is None:
        _errors["case_type_identification"] = err_invalid_case_type
    else:
        # narrow down the possible document type URLs for validation
        valid_document_type_urls = {
            iot_url
            for ct in case_type_versions
            for iot_url in ct.get("informatieobjecttypen", [])
        }

    # serializer validation prevents blank document type descriptions from being
    # configured.
    assert document_type_description, "Document type description may not be empty."
    # validate the document type reference. Note that the validation does not
    # consider versions - as soon as the document type was present with any version
    # of the case type at any point, it is allowed to go through. This *may* lead
    # to runtime errors if the document type (or its version) is no longer related
    # to the case type version that applies to the moment of registration.
    document_type_versions = client.find_informatieobjecttypen(
        catalogus=catalogus["url"],
        description=document_type_description,
    )
    if document_type_versions is None:
        _errors["document_type_description"] = err_invalid_document_type
    else:
        document_type_urls = {item["url"] for item in document_type_versions}
        # check the intersection with the known good URLs
        intersection = document_type_urls & set(valid_document_type_urls)
        if not intersection:
            _errors["document_type_description"] = err_invalid_document_type

    _files_errors = {}
    for index, file_options in enumerate(attrs.get("files", [])):
        if not (description := file_options.get("document_type_description")):
            continue
        versions = client.find_informatieobjecttypen(
            catalogus=catalogus["url"], description=description
        )
        if versions is None:
            _files_errors[index] = {
                "document_type_description": err_invalid_document_type
            }
        else:
            document_type_urls = {item["url"] for item in versions}
            # check the intersection with the known good URLs
            intersection = document_type_urls & set(valid_document_type_urls)
            if not intersection:
                _files_errors[index] = {
                    "document_type_description": err_invalid_document_type
                }

    if _files_errors:
        _errors["files"] = _files_errors

    # If there are problems with the case type or document type, there's no point
    # to continue validation that relies on these values, so bail early.
    if _errors:
        raise serializers.ValidationError(_errors)

    return {"catalogue": catalogus}


def _validate_case_type_properties(
    client: CatalogiClient,
    attrs: RegistrationOptions,
    iter_case_type_versions: CaseTypeVersionsIterator,
) -> None:
    # Make sure the property (eigenschap) related to the zaaktype exists
    if not (mappings := attrs.get("property_mappings")):
        return

    eigenschappen = []
    for version in iter_case_type_versions():
        eigenschappen += client.list_eigenschappen(zaaktype=version["url"])

    eigenschappen_names = {eigenschap["naam"] for eigenschap in eigenschappen}

    _errors: dict[int, dict] = {}
    for index, mapping in enumerate(mappings):
        if (name := mapping["eigenschap"]) in eigenschappen_names:
            continue

        msg = _(
            "Could not find a property with the name '{name}' in the case type"
        ).format(name=name)
        _errors[index] = {"eigenschap": ErrorDetail(msg, code="not-found")}

        # TODO: validate that the componentKey is a valid reference, but for that the
        # variables must be persisted before the form registration options are being
        # validated, which currently is not the case.

    if _errors:
        raise serializers.ValidationError(
            {"property_mappings": _errors},  # type: ignore
            code="invalid",
        )


def _validate_medewerker_and_family_members_roltype(
    client: CatalogiClient,
    attrs: RegistrationOptions,
    iter_case_type_versions: CaseTypeVersionsIterator,
) -> None:
    medewerker_description = attrs.get("medewerker_roltype")
    partners_description = attrs.get("partners_roltype")
    children_description = attrs.get("children_roltype")

    if not any((medewerker_description, partners_description, children_description)):
        return

    medewerker_roltypen = []
    partners_roltypen = []
    children_roltypen = []
    for version in iter_case_type_versions():
        if medewerker_description:
            medewerker_roltypen += client.list_roltypen(
                zaaktype=version["url"],
                matcher=omschrijving_matcher(medewerker_description),
            )

        if partners_description:
            partners_roltypen += client.list_roltypen(
                zaaktype=version["url"],
                matcher=omschrijving_matcher(partners_description),
            )

        if children_description:
            children_roltypen += client.list_roltypen(
                zaaktype=version["url"],
                matcher=omschrijving_matcher(children_description),
            )

        if medewerker_roltypen and partners_roltypen and children_roltypen:
            break

    error_message = _(
        "Could not find a roltype with this description related to the zaaktype."
    )
    fields_with_error = [
        field_name
        for field_name, roltypen in {
            "medewerker_roltype": medewerker_roltypen,
            "partners_roltype": partners_roltypen,
            "children_roltype": children_roltypen,
        }.items()
        if not roltypen and attrs.get(field_name)
    ]

    if fields_with_error:
        raise serializers.ValidationError(
            {field: error_message for field in fields_with_error},
            code="invalid",
        )
