"""
Implement backend functionality for core Formio (built-in) component types.

Custom component types (defined by us or third parties) need to be organized in the
adjacent custom.py module.
"""

from typing import TYPE_CHECKING

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.reverse import reverse

from csp_post_processor import post_process_html
from openforms.config.constants import UploadFileType
from openforms.config.models import GlobalConfiguration
from openforms.typing import DataMapping
from openforms.utils.urls import build_absolute_uri
from openforms.validations.service import PluginValidator

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
from ..serializers import build_serializer
from ..typing import (
    Component,
    ContentComponent,
    EditGridComponent,
    FileComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
    TextFieldComponent,
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
class TextField(BasePlugin[TextFieldComponent]):
    formatter = TextFieldFormatter

    def build_serializer_field(
        self, component: TextFieldComponent
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        validators = []
        if pattern := validate.get("pattern"):
            validators.append(
                RegexValidator(
                    pattern,
                    message=_("This value does not match the required pattern."),
                )
            )

        # Run plugin validators at the end after all basic checks have been performed.
        if plugin_ids := validate.get("plugins", []):
            validators += [PluginValidator(plugin) for plugin in plugin_ids]

        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required, allow_blank=not required, allow_null=False, **extra
        )
        return serializers.ListField(child=base) if multiple else base


@register("email")
class Email(BasePlugin):
    formatter = EmailFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.EmailField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        if validate.get("plugins", []):
            raise NotImplementedError("Plugin validators not supported yet.")

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        base = serializers.EmailField(
            required=required, allow_blank=not required, allow_null=False, **extra
        )
        return serializers.ListField(child=base) if multiple else base


@register("time")
class Time(BasePlugin):
    formatter = TimeFormatter


@register("phoneNumber")
class PhoneNumber(BasePlugin):
    formatter = PhoneNumberFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.CharField | serializers.ListField:
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        if validate.get("plugins", []):
            raise NotImplementedError("Plugin validators not supported yet.")

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        # maxLength because of the usage in appointments, even though our form builder
        # does not expose it. See `openforms.appointments.contrib.qmatic.constants`.
        if (max_length := validate.get("maxLength")) is not None:
            extra["max_length"] = max_length

        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        validators = []
        if pattern := validate.get("pattern"):
            validators.append(
                RegexValidator(
                    pattern,
                    message=_("This value does not match the required pattern."),
                )
            )
        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required, allow_blank=not required, allow_null=False, **extra
        )
        return serializers.ListField(child=base) if multiple else base


@register("file")
class File(BasePlugin[FileComponent]):
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
            mimetypes: list[str] = config.form_upload_default_file_types  # type: ignore
            component["filePattern"] = ",".join(mimetypes)
            component["file"].update(
                {
                    "allowedTypesLabels": [
                        UploadFileType(mimetype).label for mimetype in mimetypes
                    ],
                }
            )


@register("textarea")
class TextArea(BasePlugin):
    formatter = TextAreaFormatter


@register("number")
class Number(BasePlugin):
    formatter = NumberFormatter

    def build_serializer_field(
        self, component: Component
    ) -> serializers.FloatField | serializers.ListField:
        # new builder no longer exposes this, but existing forms may have multiple set
        multiple = component.get("multiple", False)
        validate = component.get("validate", {})
        required = validate.get("required", False)

        if validate.get("plugins", []):
            raise NotImplementedError("Plugin validators not supported yet.")

        extra = {}
        if max_value := validate.get("max"):
            extra["max_value"] = max_value
        if min_value := validate.get("min"):
            extra["min_value"] = min_value

        base = serializers.FloatField(
            required=required,
            allow_null=not required,
            **extra,
        )
        return serializers.ListField(child=base) if multiple else base


@register("password")
class Password(BasePlugin):
    formatter = PasswordFormatter


@register("checkbox")
class Checkbox(BasePlugin):
    formatter = CheckboxFormatter


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

    def localize(self, component: RadioComponent, language_code: str, enabled: bool):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)

    def build_serializer_field(
        self, component: RadioComponent
    ) -> serializers.ChoiceField:
        """
        Convert a radio component to a serializer field.

        A radio component allows only a single value to be selected, but selecting a
        value may not be required. The available choices are taken from the ``values``
        key, which may be set dynamically (see :meth:`mutate_config_dynamically`).
        """
        validate = component.get("validate", {})
        required = validate.get("required", False)
        choices = [(value["value"], value["label"]) for value in component["values"]]
        return serializers.ChoiceField(
            choices=choices,
            required=required,
            allow_blank=not required,
            allow_null=not required,
        )


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


@register("editgrid")
class EditGrid(BasePlugin[EditGridComponent]):
    def build_serializer_field(
        self, component: EditGridComponent
    ) -> serializers.ListField:
        validate = component.get("validate", {})
        required = validate.get("required", False)
        nested = build_serializer(
            components=component.get("components", []),
            # XXX: check out type annotations here, there's some co/contra variance
            # in play
            register=self.registry,
        )
        kwargs = {}
        if (max_length := validate.get("maxLength")) is not None:
            kwargs["max_length"] = max_length
        return serializers.ListField(
            child=nested,
            required=required,
            allow_null=not required,
            allow_empty=False,
            **kwargs,
        )
