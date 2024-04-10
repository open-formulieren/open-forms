"""
Implement backend functionality for core Formio (built-in) component types.

Custom component types (defined by us or third parties) need to be organized in the
adjacent custom.py module.
"""
from typing import TYPE_CHECKING

from rest_framework.request import Request
from rest_framework.reverse import reverse

from csp_post_processor import post_process_html
from openforms.config.constants import UploadFileType
from openforms.config.models import GlobalConfiguration
from openforms.typing import DataMapping
from openforms.utils.urls import build_absolute_uri

from ..dynamic_config.dynamic_options import add_options_to_config
from ..formatters.formio import (
    CheckboxFormatter,
    CurrencyFormatter,
    DefaultFormatter,
    EmailFormatter,
    FileFormatter,
    NumberFormatter,
    PasswordFormatter,
    PhoneNumberFormatter,
    RadioFormatter,
    SelectBoxesFormatter,
    SelectFormatter,
    SignatureFormatter,
    TextAreaFormatter,
    TextFieldFormatter,
    TimeFormatter,
)
from ..registry import BasePlugin, register
from ..typing import (
    ContentComponent,
    FileComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
)
from .translations import translate_options

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


@register("default")
class Default(BasePlugin):
    """
    Fallback for unregistered component types, implementing default behaviour.
    """

    formatter = DefaultFormatter


@register("textfield")
class TextField(BasePlugin):
    formatter = TextFieldFormatter


@register("email")
class Email(BasePlugin):
    formatter = EmailFormatter


@register("time")
class Time(BasePlugin):
    formatter = TimeFormatter


@register("phoneNumber")
class PhoneNumber(BasePlugin):
    formatter = PhoneNumberFormatter


@register("file")
class File(BasePlugin):
    formatter = FileFormatter

    @staticmethod
    def rewrite_for_request(component: FileComponent, request: Request):
        # write the upload endpoint information
        upload_endpoint = reverse("api:formio:temporary-file-upload")
        component["url"] = build_absolute_uri(upload_endpoint, request=request)

        # check if we need to apply "filePattern" modifications
        if component.get("useConfigFiletypes", False):
            config = GlobalConfiguration.get_solo()
            assert isinstance(config, GlobalConfiguration)
            component["filePattern"] = ",".join(config.form_upload_default_file_types)
            component["file"].update(
                {
                    "allowedTypesLabels": [
                        UploadFileType(mimetype).label
                        for mimetype in config.form_upload_default_file_types
                    ],
                }
            )


@register("textarea")
class TextArea(BasePlugin):
    formatter = TextAreaFormatter


@register("number")
class Number(BasePlugin):
    formatter = NumberFormatter


@register("password")
class Password(BasePlugin):
    formatter = PasswordFormatter


@register("checkbox")
class Checkbox(BasePlugin):
    formatter = CheckboxFormatter


class SelectboxesField(serializers.Serializer):

    default_error_messages = {
        "min_selected_count": _(
            "Ensure this field has at least {min_selected_count} checked options."
        ),
        "max_selected_count": _(
            "Ensure this field has no more than {max_selected_count} checked options."
        ),
    }

    def __init__(self, *args, **kwargs):
        self.min_selected_count: int | None = kwargs.pop("min_selected_count", None)
        self.max_selected_count: int | None = kwargs.pop("max_selected_count", None)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        validated_data: dict[str, bool] = super().to_internal_value(data)
        num_checked = len([value for value in validated_data.values() if value is True])

        # min_selected_count trumps required checks
        if self.min_selected_count is not None:
            if num_checked < self.min_selected_count:
                self.fail(
                    "min_selected_count", min_selected_count=self.min_selected_count
                )
        elif self.required and num_checked < 1:
            self.fail("required")

        # max checked validation is completely independent from min/required
        if self.max_selected_count is not None:
            if num_checked > self.max_selected_count:
                self.fail(
                    "max_selected_count", max_selected_count=self.max_selected_count
                )

        return validated_data


@register("selectboxes")
class SelectBoxes(BasePlugin[SelectBoxesComponent]):
    formatter = SelectBoxesFormatter

    def mutate_config_dynamically(
        self,
        component: SelectBoxesComponent,
        submission: "Submission",
        data: DataMapping,
    ) -> None:
        add_options_to_config(component, data, submission)

    def localize(
        self, component: SelectBoxesComponent, language_code: str, enabled: bool
    ):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)

    def build_serializer_field(
        self, component: SelectBoxesComponent
    ) -> serializers.Serializer:
        validate = component.get("validate", {})
        required = validate.get("required", False)

        serializer = SelectboxesField(
            required=required,
            allow_null=not required,
            min_selected_count=validate.get("minSelectedCount"),
            max_selected_count=validate.get("maxSelectedCount"),
        )
        for option in component["values"]:
            serializer.fields[option["value"]] = serializers.BooleanField(required=True)

        return serializer


@register("select")
class Select(BasePlugin[SelectComponent]):
    formatter = SelectFormatter

    def mutate_config_dynamically(
        self, component, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(
            component,
            data,
            submission,
            options_path="data.values",
        )

    def localize(self, component: SelectComponent, language_code: str, enabled: bool):
        if not (options := component.get("data", {}).get("values", [])):
            return
        translate_options(options, language_code, enabled)


@register("currency")
class Currency(BasePlugin):
    formatter = CurrencyFormatter


@register("radio")
class Radio(BasePlugin[RadioComponent]):
    formatter = RadioFormatter

    def mutate_config_dynamically(
        self, component: RadioComponent, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(component, data, submission)

    def localize(self, component: SelectComponent, language_code: str, enabled: bool):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)


@register("signature")
class Signature(BasePlugin):
    formatter = SignatureFormatter


@register("content")
class Content(BasePlugin):
    """
    Formio's WYSIWYG component.
    """

    # not really relevant as content components don't have values
    formatter = DefaultFormatter

    @staticmethod
    def rewrite_for_request(component: ContentComponent, request: Request):
        """
        Ensure that the inline styles are made compatible with Content-Security-Policy.

        .. note:: we apply Bleach and a CSS declaration allowlist as part of the
           post-processor because content components are not purely "trusted" content
           from form-designers, but can contain malicious user input if the form
           designer uses variables inside the HTML. The form submission data is passed
           as template context to these HTML blobs, posing a potential injection
           security risk.
        """
        component["html"] = post_process_html(component["html"], request)
