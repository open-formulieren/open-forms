"""
Implement backend functionality for core Formio (built-in) component types.

Custom component types (defined by us or third parties) need to be organized in the
adjacent custom.py module.
"""

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import time
from typing import TYPE_CHECKING, Any

from django.core.files.uploadedfile import UploadedFile
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    RegexValidator,
)
from django.utils.translation import gettext_lazy as _

import structlog
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.utils.formatting import lazy_format

from csp_post_processor import post_process_html
from formio_types import (
    AnyComponent,
    Checkbox,
    Columns,
    Content,
    Currency,
    EditGrid,
    Email,
    Fieldset,
    File,
    Number,
    PhoneNumber,
    Radio,
    Select,
    Selectboxes,
    Signature,
    SoftRequiredErrors,
    Textarea,
    TextField,
    Time,
)
from openforms.config.constants import UploadFileType
from openforms.config.models import GlobalConfiguration
from openforms.submissions.attachments import temporary_upload_from_url
from openforms.submissions.form_logic import process_visibility
from openforms.submissions.models import EmailVerification
from openforms.typing import JSONObject, VariableValue
from openforms.utils.json_schema import to_multiple
from openforms.utils.urls import build_absolute_uri
from openforms.validations.service import PluginValidator

from ..api.validators import MimeTypeValidator
from ..datastructures import FormioConfigurationWrapper, FormioData
from ..dynamic_config.dynamic_options import add_options_to_config
from ..formatters.formio import (
    CheckboxFormatter,
    CurrencyFormatter,
    DefaultFormatter,
    EmailFormatter,
    FileFormatter,
    NumberFormatter,
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
from ..service import as_json_schema
from ..typing import (
    ColumnsComponent,
    Component,
    ContentComponent,
    EditGridComponent,
    FieldsetComponent,
    FileComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
    TextFieldComponent,
)
from .translations import translate_options
from .utils import _normalize_pattern, sanitize_file_name

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


logger = structlog.stdlib.get_logger(__name__)


@register("default")
class DefaultPlugin(BasePlugin[Component, AnyComponent]):
    """
    Fallback for unregistered component types, implementing default behaviour.
    """

    formatter = DefaultFormatter


@register("textfield")
class TextFieldPlugin(BasePlugin[TextFieldComponent, TextField]):
    formatter = TextFieldFormatter

    @staticmethod
    def normalizer(component: TextField, value: str | float) -> str:
        if isinstance(value, int | float):
            return str(value)
        return value

    def build_serializer_field(
        self, component: TextField
    ) -> serializers.CharField | serializers.ListField:
        validate = component.validate
        required = validate is not None and validate.required

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if (max_length := (validate and validate.max_length)) is not None:
            extra["max_length"] = max_length

        # adding in the validator is more explicit than changing to serialiers.RegexField,
        # which essentially does the same.
        validators = []
        if validate and (pattern := validate.pattern):
            validators.append(
                RegexValidator(
                    _normalize_pattern(pattern),
                    message=_("This value does not match the required pattern."),
                )
            )

        # Run plugin validators at the end after all basic checks have been performed.
        if validate and (plugin_ids := validate.plugins):
            validators.append(PluginValidator(plugin_ids))

        if validators:
            extra["validators"] = validators

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=component.multiple,
            **extra,
        )
        return serializers.ListField(child=base) if component.multiple else base

    @staticmethod
    def as_json_schema(component: TextField) -> JSONObject:
        base: JSONObject = {"title": component.label, "type": "string"}
        if validate := component.validate:
            if pattern := validate.pattern:
                base["pattern"] = pattern
            if max_length := validate.max_length:
                base["maxLength"] = max_length

        return to_multiple(base) if component.multiple else base


class EmailVerificationValidator:
    message = _("The email address {value} has not been verified yet.")
    requires_context = True

    def __init__(self, component_key: str):
        self.component_key = component_key

    def __call__(self, value: str, field: serializers.Field) -> None:
        submission: Submission = field.context["submission"]
        has_verification = EmailVerification.objects.filter(
            submission=submission,
            component_key=self.component_key,
            email=value,
            verified_on__isnull=False,
        ).exists()
        if not has_verification:
            raise serializers.ValidationError(
                self.message.format(value=value), code="unverified"
            )


@register("email")
class EmailPlugin(BasePlugin[Component, Email]):
    formatter = EmailFormatter

    def build_serializer_field(
        self, component: Email
    ) -> serializers.EmailField | serializers.ListField:
        validate = component.validate
        required = validate is not None and validate.required
        verification_required = (
            component.open_forms and component.open_forms.require_verification
        )

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if validate and (max_length := validate.max_length) is not None:
            extra["max_length"] = max_length

        validators = []
        if validate and (plugin_ids := validate.plugins):
            validators.append(PluginValidator(plugin_ids))

        if verification_required:
            validators.append(EmailVerificationValidator(component.key))

        if validators:
            extra["validators"] = validators

        base = serializers.EmailField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=component.multiple,
            **extra,
        )
        return serializers.ListField(child=base) if component.multiple else base

    @staticmethod
    def as_json_schema(component: Email) -> JSONObject:
        base: JSONObject = {
            "title": component.label,
            "type": "string",
            "format": "email",
        }
        return to_multiple(base) if component.multiple else base


class FormioTimeField(serializers.TimeField):
    def validate_empty_values(self, data):
        is_empty, data = super().validate_empty_values(data)
        # base field only treats `None` as empty, but formio uses empty strings
        if data == "":
            if self.required:
                self.fail("required")
            return (True, "")
        return is_empty, data


class TimeBetweenValidator:
    def __init__(self, min_time: time, max_time: time) -> None:
        self.min_time = min_time
        self.max_time = max_time

    def __call__(self, value: time):
        # same day - straight forward comparison
        if self.min_time < self.max_time:
            if value < self.min_time:
                raise serializers.ValidationError(
                    _("Value is before minimum time"),
                    code="min_value",
                )
            if value > self.max_time:
                raise serializers.ValidationError(
                    _("Value is after maximum time"),
                    code="max_value",
                )

        # min time is on the day before the max time applies (e.g. 20:00 -> 04:00)
        else:
            if value < self.min_time and value > self.max_time:
                raise serializers.ValidationError(
                    _("Value is not between mininum and maximum time."), code="invalid"
                )


@register("time")
class TimePlugin(BasePlugin[Component, Time]):
    formatter = TimeFormatter

    def build_serializer_field(
        self, component: Time
    ) -> FormioTimeField | serializers.ListField:
        validate = component.validate
        required = validate is not None and validate.required

        validators = []

        if validate:
            match (
                min_time := (validate.min_time or None),
                max_time := (validate.max_time or None),
            ):
                case (None, None):
                    pass
                case (str(), None):
                    validators.append(MinValueValidator(time.fromisoformat(min_time)))
                case (None, str()):
                    validators.append(MaxValueValidator(time.fromisoformat(max_time)))
                case (str(), str()):
                    validators.append(
                        TimeBetweenValidator(
                            time.fromisoformat(min_time),
                            time.fromisoformat(max_time),
                        )
                    )
                case _:  # pragma: no cover
                    logger.warning(
                        "formio.unexpected_min_max_time",
                        component=component,
                        min_time=min_time,
                        max_time=max_time,
                    )

        base = FormioTimeField(
            required=required,
            allow_null=not required,
            validators=validators,
        )
        return serializers.ListField(child=base) if component.multiple else base

    @staticmethod
    def as_json_schema(component: Time) -> JSONObject:
        base: JSONObject = {
            "title": component.label,
            "type": "string",
            "format": "time",
        }
        return to_multiple(base) if component.multiple else base


@register("phoneNumber")
class PhoneNumberPlugin(BasePlugin[Component, PhoneNumber]):
    formatter = PhoneNumberFormatter

    def build_serializer_field(
        self, component: PhoneNumber
    ) -> serializers.CharField | serializers.ListField:
        validate = component.validate
        required = validate is not None and validate.required

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if validate:
            # maxLength because of the usage in appointments, even though our form builder
            # does not expose it. See `openforms.appointments.contrib.qmatic.constants`.
            if (max_length := validate.max_length) is not None:
                extra["max_length"] = max_length

            # adding in the validator is more explicit than changing to serialiers.RegexField,
            # which essentially does the same.
            validators = []
            if pattern := validate.pattern:
                validators.append(
                    RegexValidator(
                        _normalize_pattern(pattern),
                        message=_("This value does not match the required pattern."),
                    )
                )

            # Run plugin validators at the end after all basic checks have been performed.
            if plugin_ids := validate.plugins:
                validators.append(PluginValidator(plugin_ids))

            if validators:
                extra["validators"] = validators

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=component.multiple,
            **extra,
        )
        return serializers.ListField(child=base) if component.multiple else base

    @staticmethod
    def as_json_schema(component: PhoneNumber) -> JSONObject:
        pattern: str = r"^\+?[\d\s]+$"
        if (validate := component.validate) and validate.pattern:
            pattern = validate.pattern

        base: JSONObject = {
            "title": component.label,
            "type": "string",
            "pattern": pattern,
        }
        return to_multiple(base) if component.multiple else base


class FileDataSerializer(serializers.Serializer):
    url = serializers.URLField()
    form = serializers.ChoiceField(choices=[""])
    name = serializers.CharField(trim_whitespace=False)
    size = serializers.IntegerField(min_value=0)
    baseUrl = serializers.URLField()
    project = serializers.ChoiceField(choices=[""])


class FileSerializer(serializers.Serializer):
    name = serializers.CharField()
    originalName = serializers.CharField(trim_whitespace=False)
    size = serializers.IntegerField(min_value=0)
    storage = serializers.ChoiceField(choices=["url"])
    type = serializers.CharField(required=True, allow_blank=True)
    url = serializers.URLField()
    data = FileDataSerializer()  # type: ignore

    def __init__(self, *args, **kwargs) -> None:
        allowed_mime_types = kwargs.pop("allowed_mime_types", [])
        self.mime_type_validator = MimeTypeValidator(allowed_mime_types)
        super().__init__(*args, **kwargs)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        # when the file is being uploaded "temporary-file-upload" endpoint is used.
        # It has MultiPartParser, which changes the file name in sanitize_file_name,
        # including the removal of soft-hyphens.
        # Formio isn't aware of change so its "originalName" attribute may differ
        # from the file name stored in django.
        # Here we apply the same changes to the "originalName" attribute, so it won't differ
        # from the stored file name
        attrs["originalName"] = sanitize_file_name(attrs["originalName"])

        for root_key, nested_key in (
            ("url", "url"),
            ("size", "size"),
            ("originalName", "name"),
        ):
            if attrs[root_key] != attrs["data"][nested_key]:
                raise serializers.ValidationError(
                    _(
                        "The value of {root_key} must match the value of {nested_key} in 'data'."
                    ).format(
                        root_key=root_key,
                        nested_key=nested_key,
                    )
                )

        temporary_upload = temporary_upload_from_url(attrs["url"])
        if temporary_upload is None:
            raise serializers.ValidationError({"url": _("Invalid URL.")})

        if attrs["size"] != temporary_upload.file_size:
            raise serializers.ValidationError(
                {"size": _("Size does not match the uploaded file.")}
            )

        if attrs["originalName"] != temporary_upload.file_name:
            raise serializers.ValidationError(
                {"originalName": _("Name does not match the uploaded file.")}
            )

        if temporary_upload.submission != self.context["submission"]:
            raise serializers.ValidationError({"url": _("Invalid URL.")})

        with temporary_upload.content.open("rb") as infile:
            # wrap in UploadedFile just to reuse DRF validator
            uploaded_file = UploadedFile(
                file=infile,
                name=temporary_upload.file_name,
                content_type=temporary_upload.content_type,
            )
            self.mime_type_validator(uploaded_file)

        return attrs


@register("file")
class FilePlugin(BasePlugin[FileComponent, File]):
    formatter = FileFormatter

    @staticmethod
    def rewrite_for_request(component: FileComponent, request: Request):
        # write the upload endpoint information
        upload_endpoint = reverse("api:formio:temporary-file-upload")
        component["url"] = build_absolute_uri(upload_endpoint, request=request)

        # check if we need to apply "filePattern" modifications
        if component.get("useConfigFiletypes", False):
            config = GlobalConfiguration.get_solo()
            mimetypes: list[str] = config.form_upload_default_file_types  # type: ignore
            component["filePattern"] = ",".join(mimetypes)
            component["file"].update(
                {
                    "allowedTypesLabels": [
                        UploadFileType(mimetype).label for mimetype in mimetypes
                    ],
                }
            )

    def build_serializer_field(self, component: File) -> serializers.ListField:
        max_number_of_files = component.max_number_of_files
        if max_number_of_files is None and not component.multiple:
            max_number_of_files = 1
        validate = component.validate
        required = validate is not None and validate.required

        if component.use_config_filetypes:
            config = GlobalConfiguration.get_solo()
            allowed_mime_types = config.form_upload_default_file_types
        else:
            allowed_mime_types = component.file.type

        return serializers.ListField(
            max_length=max_number_of_files,
            min_length=1 if required else None,
            child=FileSerializer(allowed_mime_types=allowed_mime_types),
            required=required,
        )

    @staticmethod
    def as_json_schema(component: File) -> JSONObject:
        # fmt: off
        base: JSONObject = {
            "title": component.label,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "originalName": {"type": "string"},
                    "size": {"type": "number", "description": "Size in bytes"},
                    "storage": {"type": "string"},
                    "type": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "baseUrl": {"type": "string", "format": "uri"},
                            "form": {"type": "string"},
                            "name": {"type": "string"},
                            "project": {"type": "string"},
                            "size": {"type": "number", "description": "Size in bytes"},
                            "url": {"type": "string", "format": "uri"},
                        },
                        "required": ["baseUrl", "form", "name", "project", "size", "url"],
                    },
                },
                "required": ["name", "originalName", "size", "storage", "type", "url", "data"],
            },
        }
        # fmt: on
        return base


@register("textarea")
class TextAreaPlugin(BasePlugin[Component, Textarea]):
    formatter = TextAreaFormatter

    def build_serializer_field(
        self, component: Textarea
    ) -> serializers.CharField | serializers.ListField:
        validate = component.validate
        required = validate is not None and validate.required

        # dynamically add in more kwargs based on the component configuration
        extra = {}
        if validate and (max_length := validate.max_length) is not None:
            extra["max_length"] = max_length

        base = serializers.CharField(
            required=required,
            allow_blank=not required,
            # FIXME: should always be False, but formio client sends `null` for
            # untouched fields :( See #4068
            allow_null=component.multiple,
            **extra,
        )
        return serializers.ListField(child=base) if component.multiple else base

    @staticmethod
    def as_json_schema(component: Textarea) -> JSONObject:
        base: JSONObject = {"title": component.label, "type": "string"}
        if validate := component.validate:
            if pattern := validate.pattern:
                base["pattern"] = pattern
            if max_length := validate.max_length:
                base["maxLength"] = max_length
        return to_multiple(base) if component.multiple else base


@register("number")
class NumberPlugin(BasePlugin[Component, Number]):
    formatter = NumberFormatter

    def build_serializer_field(self, component: Number) -> serializers.FloatField:
        # new builder no longer exposes this, but existing forms may have multiple set
        validate = component.validate
        required = validate is not None and validate.required

        extra = {}
        if validate:
            if (max_value := validate.max) is not None:
                extra["max_value"] = max_value
            if (min_value := validate.min) is not None:
                extra["min_value"] = min_value

            validators = []
            if plugin_ids := validate.plugins:
                validators.append(PluginValidator(plugin_ids))

            if validators:
                extra["validators"] = validators

        return serializers.FloatField(
            required=required, allow_null=not required, **extra
        )

    @staticmethod
    def as_json_schema(component: Number) -> JSONObject:
        base: JSONObject = {"title": component.label, "type": "number"}
        if validate := component.validate:
            if min_value := validate.min:
                base["minimum"] = min_value
            if max_value := validate.max:
                base["maximum"] = max_value
        return base


def validate_required_checkbox(value: bool) -> None:
    """
    A required checkbox in Formio terms means it *must* be checked.
    """
    if not value:
        raise serializers.ValidationError(
            _("Checkbox must be checked."), code="invalid"
        )


@register("checkbox")
class CheckboxPlugin(BasePlugin[Component, Checkbox]):
    formatter = CheckboxFormatter

    def build_serializer_field(self, component: Checkbox) -> serializers.BooleanField:
        validate = component.validate
        required = validate is not None and validate.required

        # dynamically add in more kwargs based on the component configuration
        extra = {}

        validators = []
        if required:
            validators.append(validate_required_checkbox)
        if validate and (plugin_ids := validate.plugins):
            validators.append(PluginValidator(plugin_ids))

        if validators:
            extra["validators"] = validators

        return serializers.BooleanField(**extra)

    @staticmethod
    def as_json_schema(component: Checkbox) -> JSONObject:
        base: JSONObject = {"title": component.label, "type": "boolean"}
        return base


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

        if not self.required and num_checked == 0:
            return validated_data

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
class SelectBoxesPlugin(BasePlugin[SelectBoxesComponent, Selectboxes]):
    formatter = SelectBoxesFormatter

    def mutate_config_dynamically(
        self,
        component: SelectBoxesComponent,
        submission: "Submission",
        data: FormioData,
    ) -> None:
        add_options_to_config(component, data, submission)

    def localize(
        self, component: SelectBoxesComponent, language_code: str, enabled: bool
    ):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)

    def build_serializer_field(self, component: Selectboxes) -> serializers.Serializer:
        validate = component.validate
        required = validate is not None and validate.required

        serializer = SelectboxesField(
            required=required,
            allow_null=not required,
            min_selected_count=validate and validate.min_selected_count,
            max_selected_count=validate and validate.max_selected_count,
        )
        for option in component.values:
            serializer.fields[option.value] = serializers.BooleanField(required=True)

        return serializer

    @staticmethod
    def as_json_schema(component: Selectboxes) -> JSONObject:
        values = component.values

        base: JSONObject = {"title": component.label, "type": "object"}
        # Note: the 'values' will be a list with a single empty option if the data
        # source is another variable or reference lists, AND the configuration was not
        # updated before generating the schema.
        if values and not (len(values) == 1 and values[0].label == ""):
            properties: JSONObject = {
                option.value: {"type": "boolean"} for option in values
            }
            base.update(
                {
                    "properties": properties,
                    "required": list(properties.keys()),
                    "additionalProperties": False,
                }
            )
        else:
            base["additionalProperties"] = True

        return base

    @staticmethod
    def test_conditional(
        component: SelectBoxesComponent,
        value: VariableValue,
        compare_value: VariableValue,
    ) -> bool:
        # Selectboxes need some special attention as we need to check whether the
        # value corresponding to the key ``compare_value`` is set to ``True`` in the
        # dictionary.
        # NOTE: the previous implementation defaulted to the direct comparison, but
        # this is not useful for selectboxes components, because a user can only set
        # a single compare value, not an object.
        assert isinstance(value, dict)
        assert isinstance(compare_value, str)
        result = value.get(compare_value, False)
        assert isinstance(result, bool)
        return result


@register("select")
class SelectPlugin(BasePlugin[SelectComponent, Select]):
    formatter = SelectFormatter

    def mutate_config_dynamically(
        self, component, submission: "Submission", data: FormioData
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

    def build_serializer_field(self, component: Select) -> serializers.ChoiceField:
        validate = component.validate
        required = validate is not None and validate.required
        choices = [(value.value, value.label) for value in component.data.values]

        # map multiple false/true to the respective serializer field configuration
        field_kwargs: dict[str, Any]
        match component:
            case Select(multiple=True):
                field_cls = serializers.MultipleChoiceField
                field_kwargs = {"allow_empty": not required}
            case _:
                field_cls = serializers.ChoiceField
                field_kwargs = {}

        return field_cls(
            choices=choices,
            required=required,
            # See #4084 - form builder bug causes empty option to be added. allow_blank
            # is therefore required for select with `multiple: true` too.
            allow_blank=not required,
            **field_kwargs,
        )

    @staticmethod
    def as_json_schema(component: Select) -> JSONObject:
        values = component.data.values

        base: JSONObject = {"type": "string"}
        # Note: the 'values' will be a list with a single empty option if the data
        # source is another variable or reference lists, AND the configuration was not
        # updated before generating the schema.
        if values and not (len(values) == 1 and values[0].label == ""):
            # Take into account an unfilled field
            base["enum"] = [option.value for option in values] + [""]

        if component.multiple:
            base = {"type": "array", "items": base}

        base["title"] = component.label
        return base


@register("currency")
class CurrencyPlugin(BasePlugin[Component, Currency]):
    formatter = CurrencyFormatter

    def build_serializer_field(self, component: Currency) -> serializers.FloatField:
        validate = component.validate
        required = validate is not None and validate.required

        extra = {}
        if validate:
            if (max_value := validate.max) is not None:
                extra["max_value"] = max_value
            if (min_value := validate.min) is not None:
                extra["min_value"] = min_value

            validators = []
            if plugin_ids := validate.plugins:
                validators.append(PluginValidator(plugin_ids))

            if validators:
                extra["validators"] = validators

        return serializers.FloatField(
            required=required, allow_null=not required, **extra
        )

    @staticmethod
    def as_json_schema(component: Currency) -> JSONObject:
        base: JSONObject = {"title": component.label, "type": "number"}
        if validate := component.validate:
            if min_value := validate.min:
                base["minimum"] = min_value
            if max_value := validate.max:
                base["maximum"] = max_value
        return base


@register("radio")
class RadioPlugin(BasePlugin[RadioComponent, Radio]):
    formatter = RadioFormatter

    def mutate_config_dynamically(
        self, component: RadioComponent, submission: "Submission", data: FormioData
    ) -> None:
        add_options_to_config(component, data, submission)

    def localize(self, component: RadioComponent, language_code: str, enabled: bool):
        if not (options := component.get("values", [])):
            return
        translate_options(options, language_code, enabled)

    def build_serializer_field(self, component: Radio) -> serializers.ChoiceField:
        """
        Convert a radio component to a serializer field.

        A radio component allows only a single value to be selected, but selecting a
        value may not be required. The available choices are taken from the ``values``
        key, which may be set dynamically (see :meth:`mutate_config_dynamically`).
        """
        validate = component.validate
        required = validate is not None and validate.required
        choices = [(value.value, value.label) for value in component.values]
        return serializers.ChoiceField(
            choices=choices,
            required=required,
            allow_blank=not required,
            allow_null=not required,
        )

    @staticmethod
    def as_json_schema(component: Radio) -> JSONObject:
        values = component.values

        base: JSONObject = {"title": component.label, "type": "string"}
        # Note: the 'values' will be a list with a single empty option if the data
        # source is another variable or reference lists, AND the configuration was not
        # updated before generating the schema.
        # FIXME: this single empty option should not be present with the builder - fixup
        # the data/configuration that violates this assumption.
        if values and not (len(values) == 1 and values[0].label == ""):
            # Take into account an unfilled field
            base["enum"] = [option.value for option in values] + [""]

        return base


@register("signature")
class SignaturePlugin(BasePlugin[Component, Signature]):
    formatter = SignatureFormatter

    def build_serializer_field(self, component: Signature) -> serializers.CharField:
        validate = component.validate
        required = validate is not None and validate.required
        return serializers.CharField(required=required, allow_blank=not required)

    @staticmethod
    def as_json_schema(component: Signature) -> JSONObject:
        base: JSONObject = {
            "title": component.label,
            "type": "string",
            "format": "base64",
        }
        return base


@register("content")
class ContentPlugin(BasePlugin[ContentComponent, Content]):
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


class EditGridField(serializers.Field):
    """
    A variant of :class:`serializers.ListField`.

    The same child serializer cannot be applied for each item in the list of values,
    since the field validation parameters depend on the input data/conditionals.

    For each item, a dynamic serializer is set up on the fly to perform input
    validation.
    """

    initial = []
    default_error_messages = {
        "not_a_list": _('Expected a list of items but got type "{input_type}".'),
        "empty": _("This list may not be empty."),
        "min_length": _("Ensure this field has at least {min_length} elements."),
        "max_length": _("Ensure this field has no more than {max_length} elements."),
    }

    def __init__(self, **kwargs):
        self.registry = kwargs.pop("registry")
        self.components: Sequence[AnyComponent] = kwargs.pop("components", [])
        self.allow_empty = kwargs.pop("allow_empty", True)
        self.max_length = kwargs.pop("max_length", None)
        self.min_length = kwargs.pop("min_length", None)
        super().__init__(**kwargs)
        if self.max_length is not None:
            message = lazy_format(
                self.error_messages["max_length"], max_length=self.max_length
            )
            self.validators.append(MaxLengthValidator(self.max_length, message=message))
        if self.min_length is not None:
            message = lazy_format(
                self.error_messages["min_length"], min_length=self.min_length
            )
            self.validators.append(MinLengthValidator(self.min_length, message=message))

    def get_value(self, dictionary):
        # We don't bother with html or partial serializers
        return dictionary.get(self.field_name, serializers.empty)

    def to_internal_value(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if isinstance(data, str | Mapping) or not hasattr(data, "__iter__"):
            self.fail("not_a_list", input_type=type(data).__name__)
        if not self.allow_empty and len(data) == 0:
            self.fail("empty")
        return self.run_child_validation(data)

    def to_representation(self, value: list):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        child = self._build_child()
        return [
            child.to_representation(item) if item is not None else None
            for item in value
        ]

    def _build_child(self, **kwargs):
        return build_serializer(
            components=self.components,
            # XXX: check out type annotations here, there's some co/contra variance
            # in play
            register=self.registry,
            **kwargs,
        )

    def run_child_validation(self, data):
        result = []
        errors = {}

        for idx, item in enumerate(data):
            # given the local scope of data, build a nested serializer for the component
            # configuration and apply the dynamic hide/visible logic to it.
            # Note that we add the editgrid key as container so that the
            # conditional.when values resolve, as these look like `editgridparent.child`.
            data = FormioData({**self.root.initial_data, self.field_name: item}).data
            nested_serializer = self._build_child(data=data)

            # this is explicitly bound to the parent because we need to have access to the
            # context of the parent in the children
            nested_serializer.bind(field_name=self.field_name, parent=self)

            try:
                result.append(nested_serializer.run_validation(item))
            except serializers.ValidationError as e:
                errors[idx] = e.detail

        if not errors:
            return result
        raise serializers.ValidationError(errors)


@register("editgrid")
class EditGridPlugin(BasePlugin[EditGridComponent, EditGrid]):
    def build_serializer_field(self, component: EditGrid) -> EditGridField:
        validate = component.validate
        required = validate is not None and validate.required
        kwargs = {}
        if validate and (max_length := validate.max_length) is not None:
            kwargs["max_length"] = max_length
        return EditGridField(
            components=component.components,
            registry=self.registry,
            required=required,
            allow_null=not required,
            allow_empty=not required,
            **kwargs,
        )

    @staticmethod
    def as_json_schema(component: EditGrid) -> JSONObject:
        # Build the edit grid object properties by iterating over the child components
        properties = {}
        for child in component.components:
            schema = as_json_schema(child)
            match child:
                case Content() | SoftRequiredErrors():
                    continue
                case Fieldset() | Columns():
                    assert isinstance(schema, list)
                    for child_schema in schema:
                        properties.update(child_schema)
                case _:
                    properties[child.key] = schema

        base: JSONObject = {
            "title": component.label,
            "type": "array",
            "items": {
                "type": "object",
                "properties": properties,
                "required": list(properties.keys()),
                "additionalProperties": False,
            },
        }

        if validate := component.validate:
            if max_length := validate.max_length:
                base["maxItems"] = max_length

        return base

    @staticmethod
    def apply_visibility(
        component: EditGridComponent,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        parent_hidden: bool,
        ignore_hidden_property: bool,
        get_evaluation_data: Callable | None = None,
    ):
        key = component["key"]
        # We only need to process children if the value was not already cleared.
        if not (edit_grid_data := data[key]):
            return

        # We might be dealing with nested editgrids
        outer_get_evaluation_data = (
            get_evaluation_data if get_evaluation_data else lambda x: x
        )

        # If the hidden property of the parent should be ignored, so should it for its
        # children.
        components_to_ignore_hidden = (
            set(child["key"] for child in component["components"])
            if ignore_hidden_property
            else None
        )
        edit_grid_data_new = []

        # For evaluation of the conditionals, we only care about the current item, so we
        # set it to the editgrid data directly. Note that we can create a copy of the
        # complete context just once, because components inside an editgrid item cannot
        # affect components outside the editgrid.
        inner_evaluation_data = deepcopy(data)

        def get_evaluation_data(item_data_: FormioData) -> FormioData:
            inner_evaluation_data[key] = item_data_
            return outer_get_evaluation_data(inner_evaluation_data)

        for item_data in edit_grid_data:
            process_visibility(
                component,
                item_data,
                wrapper,
                parent_hidden=parent_hidden,
                get_evaluation_data=get_evaluation_data,
                components_to_ignore_hidden=components_to_ignore_hidden,
            )
            edit_grid_data_new.append(item_data)

        data[key] = edit_grid_data_new


@register("columns")
class ColumnsPlugin(BasePlugin[ColumnsComponent, Columns]):
    @staticmethod
    def apply_visibility(
        component: ColumnsComponent,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        parent_hidden: bool,
        ignore_hidden_property: bool,
        get_evaluation_data: Callable | None = None,
    ):
        for column in component["columns"]:
            # If the hidden property of the parent should be ignored, so should it for
            # its children.
            components_to_ignore_hidden = (
                set(child["key"] for child in column["components"])
                if ignore_hidden_property
                else None
            )

            process_visibility(
                column,
                data,
                wrapper,
                parent_hidden=parent_hidden,
                get_evaluation_data=get_evaluation_data,
                components_to_ignore_hidden=components_to_ignore_hidden,
            )


@register("fieldset")
class FieldsetPlugin(BasePlugin[FieldsetComponent, Fieldset]):
    @staticmethod
    def apply_visibility(
        component: FieldsetComponent,
        data: FormioData,
        wrapper: FormioConfigurationWrapper,
        *,
        parent_hidden: bool,
        ignore_hidden_property: bool,
        get_evaluation_data: Callable | None = None,
    ):
        # If the hidden property of the parent should be ignored, so should it for
        # its children.
        components_to_ignore_hidden = (
            set(child["key"] for child in component["components"])
            if ignore_hidden_property
            else None
        )

        # We need to process the children, so we just pass the component as the
        # configuration.
        process_visibility(
            component,
            data,
            wrapper,
            parent_hidden=parent_hidden,
            get_evaluation_data=get_evaluation_data,
            components_to_ignore_hidden=components_to_ignore_hidden,
        )
