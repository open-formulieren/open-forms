from collections.abc import Iterator
from functools import partial
from typing import Protocol, TypedDict

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ape_pie import InvalidURLError
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.api.fields import PrimaryKeyRelatedAsChoicesField
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


class ZaakOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    zgw_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ZGWApiGroupConfig.objects.exclude(
            Q(zrc_service=None) | Q(drc_service=None) | Q(ztc_service=None)
        ),
        help_text=_("Which ZGW API set to use."),
        label=_("ZGW API set"),
    )
    # TODO: if selected, the informatieobjecttypen from file components should also be
    # limited to this catalogue, but that requires moving the registration options from
    # the component configuration to the registration options!
    catalogue = CatalogueSerializer(
        label=_("catalogue"),
        required=False,
        help_text=_(
            "The catalogue in the catalogi API from the selected API group. This "
            "overrides the catalogue specified in the API group, if it's set. Case "
            "and document types specified will be resolved against this catalogue."
        ),
    )
    case_type_identification = serializers.CharField(
        required=False,  # either this field or zaaktype (legacy) must be provided
        label=_("Case type identification"),
        help_text=_(
            "The case type will be retrieved in the specified catalogue. The version "
            "will automatically be selected based on the submission completion "
            "timestamp. When you specify this field, you MUST also specify a catalogue."
        ),
        default="",
        allow_blank=True,
    )
    document_type_description = serializers.CharField(
        required=False,  # either htis field or informatieobjecttype (legacy) must be provided
        label=_("Document type description"),
        help_text=_(
            "The document type will be retrived in the specified catalogue. The version "
            "will automatically be selected based on the submission completion "
            "timestamp. When you specify this field, you MUST also specify the case "
            "type via its identification. Only document types related to the case type "
            "are valid."
        ),
        default="",
        allow_blank=True,
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

    # DeprecationWarning - deprecated, will be removed in OF 4.0
    zaaktype = serializers.URLField(
        help_text=_("URL of the ZAAKTYPE in the Catalogi API"),
        required=False,
        allow_blank=True,
        default="",
    )
    informatieobjecttype = serializers.URLField(
        help_text=_("URL of the INFORMATIEOBJECTTYPE in the Catalogi API"),
        required=False,
        allow_blank=True,
        default="",
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

    # Objects API
    objects_api_group = PrimaryKeyRelatedAsChoicesField(
        queryset=ObjectsAPIGroupConfig.objects.exclude(
            Q(objects_service=None) | Q(objecttypes_service=None)
        ),
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

        # Legacy forms will have zaaktype set, new forms can set case_type_identification.
        # Both may be set - in that case, `case_type_identification` is preferred.
        if not attrs["case_type_identification"] and not attrs["zaaktype"]:
            raise serializers.ValidationError(
                {
                    "case_type_identification": _("You must specify a case type."),
                },
                code="required",
            )

        # Legacy forms will have informatieobjecttype set, new forms can set
        # document_type_description. Both may be set - in that case, `document_type_description`
        # is preferred.
        if not attrs["document_type_description"] and not attrs["informatieobjecttype"]:
            raise serializers.ValidationError(
                {
                    "document_type_description": _("You must specify a document type"),
                },
                code="required",
            )

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

        _validate_against_catalogi_api(attrs)

        if attrs.get("objecttype"):
            _validate_against_objects_api_group(attrs)

        return attrs


class CaseTypeVersionsIterator(Protocol):
    def __call__(self, case_type_identification: str) -> Iterator[CaseType]: ...


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

        if catalogue := result["catalogue"]:
            iter_case_type_versions = partial(
                _iter_case_type_versions, client, catalogue
            )
        else:
            iter_case_type_versions = None

        _validate_case_type_properties(
            client, attrs, iter_case_type_versions=iter_case_type_versions
        )
        _validate_medewerker_and_partners_roltype(
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
    catalogue: Catalogus | None


def _validate_catalogue_case_and_doc_type(
    client: CatalogiClient, attrs: RegistrationOptions
) -> _CatalogueAndTypeValidationResult:
    _errors = {}

    api_group = attrs["zgw_api_group"]
    catalogus = None
    catalogue_option = attrs.get("catalogue")

    case_type_identification = attrs["case_type_identification"]
    document_type_description = attrs["document_type_description"]

    # legacy
    case_type_url = attrs["zaaktype"]
    document_type_url = attrs["informatieobjecttype"]

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

    err_invalid_case_type = ErrorDetail(
        _("The provided zaaktype does not exist in the specified Catalogi API."),  # type: ignore
        code="not-found",
    )
    err_invalid_document_type = ErrorDetail(
        _(
            "The provided informatieobjecttype does not exist in the selected case "
            "type or Catalogi API."
        ),  # type: ignore
        code="not-found",
    )

    # DB check constraint + serializer validation guarantee that both `domain` and
    # `rsin` or none of them are empty at the same time
    if case_type_identification and (not domain):
        raise serializers.ValidationError(
            {
                "catalogue": _(
                    "You must specify a catalogue when passing a case type "
                    "identification."
                ),
            },
            code="required",
        )

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

        valid_document_type_urls = catalogus["informatieobjecttypen"]

        # if a case type identification is provided, we validate (and use) it, otherwise
        # we must fall back to the legacy zaaktype url. Earlier validation guarantees
        # either one is provided (possibly both, but then we ignore the legacy URL).
        if case_type_identification:
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

        elif case_type_url not in catalogus["zaaktypen"]:
            _errors["zaaktype"] = err_invalid_case_type

        # validate the document type reference. Note that the validation does not
        # consider versions - as soon as the document type was present with any version
        # of the case type at any point, it is allowed to go through. This *may* lead
        # to runtime errors if the document type (or its version) is no longer related
        # to the case type version that applies to the moment of registration.
        if document_type_description:
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

        # Validate document type URL reference against possible valid URLs.
        elif document_type_url not in valid_document_type_urls:
            _errors["informatieobjecttype"] = err_invalid_document_type

    else:
        try:
            zaaktype_response = client.get(attrs["zaaktype"])
            zaaktype_ok = zaaktype_response.status_code == 200
        except InvalidURLError:
            zaaktype_ok = False
        if not zaaktype_ok:
            _errors["zaaktype"] = err_invalid_case_type

        try:
            document_type_response = client.get(attrs["informatieobjecttype"])
            document_type_ok = document_type_response.status_code == 200
        except InvalidURLError:
            document_type_ok = False
        if not document_type_ok:
            _errors["informatieobjecttype"] = err_invalid_document_type

    # If there are problems with the case type or document type, there's no point
    # to continue validation that relies on these values, so bail early.
    if _errors:
        raise serializers.ValidationError(_errors)

    return {"catalogue": catalogus}


def _validate_case_type_properties(
    client: CatalogiClient,
    attrs: RegistrationOptions,
    iter_case_type_versions: CaseTypeVersionsIterator | None,
) -> None:
    # Make sure the property (eigenschap) related to the zaaktype exists
    if not (mappings := attrs.get("property_mappings")):
        return

    if case_type_identification := attrs["case_type_identification"]:
        assert iter_case_type_versions is not None
        eigenschappen = []
        for version in iter_case_type_versions(case_type_identification):
            eigenschappen += client.list_eigenschappen(zaaktype=version["url"])
    else:  # DeprecationWarning
        eigenschappen = client.list_eigenschappen(zaaktype=attrs["zaaktype"])

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


def _validate_medewerker_and_partners_roltype(
    client: CatalogiClient,
    attrs: RegistrationOptions,
    iter_case_type_versions: CaseTypeVersionsIterator | None,
) -> None:
    medewerker_description = attrs.get("medewerker_roltype")
    partners_description = attrs.get("partners_roltype")

    if not medewerker_description and not partners_description:
        return

    medewerker_roltypen = []
    partners_roltypen = []
    if case_type_identification := attrs["case_type_identification"]:
        assert iter_case_type_versions is not None
        for version in iter_case_type_versions(case_type_identification):
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

            if medewerker_roltypen and partners_roltypen:
                break

    else:  # DeprecationWarning
        if medewerker_description:
            medewerker_roltypen += client.list_roltypen(
                zaaktype=attrs["zaaktype"],
                matcher=omschrijving_matcher(medewerker_description),
            )
        if partners_description:
            partners_roltypen += client.list_roltypen(
                zaaktype=attrs["zaaktype"],
                matcher=omschrijving_matcher(partners_description),
            )

    error_message = _(
        "Could not find a roltype with this description related to the zaaktype."
    )
    fields_with_error = [
        field_name
        for field_name, roltypen in {
            "medewerker_roltype": medewerker_roltypen,
            "partners_roltype": partners_roltypen,
        }.items()
        if not roltypen and attrs.get(field_name)
    ]

    if fields_with_error:
        raise serializers.ValidationError(
            {field: error_message for field in fields_with_error},
            code="invalid",
        )
