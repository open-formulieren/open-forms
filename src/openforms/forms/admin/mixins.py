from django.utils.encoding import force_str
from django.utils.translation import gettext as _

from flags.state import flag_enabled
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from formio_types import (
    BSN,
    AddressNL,
    AnyComponent,
    Checkbox,
    Children,
    CosignV2,
    Currency,
    CustomerProfile,
    Date,
    DateTime,
    EditGrid,
    Email,
    File,
    Iban,
    LicensePlate,
    Map,
    NpFamilyMembers,
    Number,
    Partners,
    PhoneNumber,
    Postcode,
    Radio,
    Select,
    Selectboxes,
    Signature,
    Textarea,
    TextField,
    Time,
)
from formio_types.datetime import FormioDateTime
from formio_types.file import FileOptions
from formio_types.select import SelectData
from openforms.config.constants import UploadFileType
from openforms.config.models import (
    GlobalConfiguration,
    MapTileLayer,
    MapWMSTileLayer,
    RichTextColor,
)
from openforms.formio.registry import register as component_registry
from openforms.typing import JSONValue


def get_rich_text_colors():
    colors = list(RichTextColor.objects.values("color", "label"))
    if not colors:
        colors = [
            {"color": "red", "label": force_str(_("Red"))},
        ]
    return colors


def get_map_tile_layers():
    return list(MapTileLayer.objects.values("identifier", "url", "label"))


def get_wms_layers():
    return list(MapWMSTileLayer.objects.values("uuid", "name", "url"))


type EmptyValueOption = tuple[str, bool, JSONValue]
"""
Data meaning: (component_type, multiple or not, associated empty value).
"""


def get_component_empty_values():
    # hack to pass the empty values, as it's not readily available in the
    # formio-renderer or formio-builder...
    # FIXME: build a proper solution for this.
    empty_values: list[EmptyValueOption] = []
    for component_plugin in component_registry:
        component_type = component_plugin.identifier
        for multiple in (True, False):
            _component: AnyComponent
            match component_type:
                case "textfield":
                    _component = TextField(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "email":
                    _component = Email(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "date":
                    _component = Date(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "datetime":
                    _component = DateTime(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=FormioDateTime([] if multiple else None),
                    )
                case "time":
                    _component = Time(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "phoneNumber":
                    _component = PhoneNumber(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "postcode":
                    _component = Postcode(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "file":
                    _component = File(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        file=FileOptions(type=[]),
                        file_pattern="",
                    )
                case "textarea":
                    _component = Textarea(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "number":
                    if multiple:
                        continue
                    _component = Number(key="dummy", label="Dummy")
                case "checkbox":
                    if multiple:
                        continue
                    _component = Checkbox(key="dummy", label="Dummy")
                case "selectboxes":
                    if multiple:
                        continue
                    _component = Selectboxes(key="dummy", label="Dummy", values=[])
                case "select":
                    _component = Select(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                        data=SelectData(),
                    )
                case "currency":
                    if multiple:
                        continue
                    _component = Currency(key="dummy", label="Dummy")
                case "radio":
                    if multiple:
                        continue
                    _component = Radio(key="dummy", label="Dummy", values=[])
                case "iban":
                    _component = Iban(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "licenseplate":
                    _component = LicensePlate(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "bsn":
                    _component = BSN(
                        key="dummy",
                        label="Dummy",
                        multiple=multiple,
                        default_value=[] if multiple else "",
                    )
                case "npFamilyMembers":
                    if multiple:
                        continue
                    _component = NpFamilyMembers(key="dummy", label="Dummy")
                case "signature":
                    if multiple:
                        continue
                    _component = Signature(key="dummy", label="Dummy")
                case "cosign":
                    if multiple:
                        continue
                    _component = CosignV2(key="dummy", label="Dummy")
                case "map":
                    if multiple:
                        continue
                    _component = Map(key="dummy", label="Dummy")
                case "editgrid":
                    if multiple:
                        continue
                    _component = EditGrid(
                        key="dummy", label="Dummy", group_label="", components=[]
                    )
                case "addressNL":
                    if multiple:
                        continue
                    _component = AddressNL(key="dummy", label="Dummy")
                case "partners":
                    if multiple:
                        continue
                    _component = Partners(key="dummy", label="Dummy")
                case "children":
                    if multiple:
                        continue
                    _component = Children(key="dummy", label="Dummy")
                case "customerProfile":
                    if multiple:
                        continue
                    _component = CustomerProfile(key="dummy", label="Dummy")
                case (
                    "default"
                    | "content"
                    | "columns"
                    | "fieldset"
                    | "softRequiredErrors"
                    | "coSign"
                    | "npfamilyMembers"
                ):
                    continue
                case _:  # pragma: no cover
                    raise NotImplementedError(f"Type {component_type} not implemented.")

            empty_value = component_registry.get_empty_value(_component)
            empty_values.append((component_type, multiple, empty_value))
    return empty_values


class FormioConfigMixin:
    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        config = GlobalConfiguration.get_solo()
        context.update(
            {
                "required_default": config.form_fields_required_default,
                "rich_text_colors": get_rich_text_colors(),
                "map_tile_layers": get_map_tile_layers(),
                "wms_layers": get_wms_layers(),
                "upload_filetypes": [
                    {"label": label, "value": value}
                    for value, label in UploadFileType.choices
                ],
                "feature_flags": {
                    "ZGW_APIS_INCLUDE_DRAFTS": flag_enabled(
                        "ZGW_APIS_INCLUDE_DRAFTS", request=request
                    ),
                },
                "confidentiality_levels": [
                    {"label": label, "value": value}
                    for value, label in VertrouwelijkheidsAanduidingen.choices
                ],
                "component_empty_values": get_component_empty_values(),
            }
        )

        return super().render_change_form(request, context, add, change, form_url, obj)
