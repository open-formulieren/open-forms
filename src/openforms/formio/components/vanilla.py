"""
Implement backend functionality for core Formio (built-in) component types.

Custom component types (defined by us or third parties) need to be organized in the
adjacent custom.py module.
"""
from typing import TYPE_CHECKING, Literal

from rest_framework.request import Request
from rest_framework.reverse import reverse

from csp_post_processor import post_process_html
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
from ..typing import Component

if TYPE_CHECKING:  # pragma: nocover
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


class FileComponent(Component):
    storage: Literal["url"]
    url: str
    useConfigFiletypes: bool
    filePattern: str


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
            component["filePattern"] = ",".join(config.form_upload_default_file_types)


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


@register("selectboxes")
class SelectBoxes(BasePlugin):
    formatter = SelectBoxesFormatter

    def mutate_config_dynamically(
        self, component: Component, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(component, data, submission)


@register("select")
class Select(BasePlugin):
    formatter = SelectFormatter

    def mutate_config_dynamically(
        self, component: Component, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(
            component,
            data,
            submission,
            options_path="data.values",
        )


@register("currency")
class Currency(BasePlugin):
    formatter = CurrencyFormatter


@register("radio")
class Radio(BasePlugin):
    formatter = RadioFormatter

    def mutate_config_dynamically(
        self, component: Component, submission: "Submission", data: DataMapping
    ) -> None:
        add_options_to_config(component, data, submission)


@register("signature")
class Signature(BasePlugin):
    formatter = SignatureFormatter


class ContentComponent(Component):
    html: str


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
