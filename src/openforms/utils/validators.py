from typing import List, Optional, Type

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.template import Context, Template, TemplateSyntaxError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.redirect import allow_redirect_url

validate_digits = RegexValidator(
    regex="^[0-9]+$", message=_("Expected a numerical value.")
)


class Proef11ValidatorBase:
    value_size = NotImplemented
    error_messages = {
        "too_short": NotImplemented,
        "wrong": NotImplemented,
    }

    def __call__(self, value):
        """
        Validates that a string value is a valid 11-proef number (BSN, RSIN etc) by applying the
        '11-proef' checking.
        :param value: String object representing a presumably good 11-proef number.
        """
        # Initial sanity checks.
        validate_digits(value)
        if len(value) != self.value_size:
            raise ValidationError(
                self.error_messages["too_short"],
                params={"size": self.value_size},
                code="invalid",
            )

        # 11-proef check.
        total = 0
        for multiplier, char in enumerate(reversed(value), start=1):
            if multiplier == 1:
                total += -multiplier * int(char)
            else:
                total += multiplier * int(char)

        if total % 11 != 0:
            raise ValidationError(self.error_messages["wrong"])


@deconstructible
class BSNValidator(Proef11ValidatorBase):
    """
    Validate a BSN value by applying the "11-proef".
    """

    value_size = 9
    error_messages = {
        "too_short": _("BSN should have %(size)i characters."),
        "wrong": _("Invalid BSN."),
    }


@deconstructible
class RSINValidator(Proef11ValidatorBase):
    """
    Validate a RSIN value by applying the "11-proef".
    """

    value_size = 9
    error_messages = {
        "too_short": _("RSIN should have %(size)i characters."),
        "wrong": _("Invalid RSIN."),
    }


validate_bsn = BSNValidator()
validate_rsin = RSINValidator()


@deconstructible
class UniqueValuesValidator:
    """
    Validate a collection of unique values.
    """

    message = _("Values must be unique")
    code = "invalid"

    def __call__(self, value: List[str]):
        uniq = set(value)
        if len(uniq) != len(value):
            raise ValidationError(self.message, code=self.code)


@deconstructible
class AllowedRedirectValidator:
    """
    Validate that a redirect target is not an open redirect.
    """

    message = _("URL is not on the domain whitelist")
    code = "invalid"

    def __call__(self, value: str):
        if not allow_redirect_url(value):
            raise ValidationError(self.message, code=self.code)


@deconstructible
class SerializerValidator:
    """
    Validate a value against a DRF serializer class.
    """

    message = _("The data shape does not match the expected shape: {errors}")
    code = "invalid"

    def __init__(self, serializer_cls: Type[serializers.Serializer], many=False):
        self.serializer_cls = serializer_cls
        self.many = many

    def __call__(self, value):
        if not value:
            return

        serializer = self.serializer_cls(data=value, many=self.many)
        if not serializer.is_valid():
            raise ValidationError(
                self.message.format(errors=serializer.errors),
                code=self.code,
            )


@deconstructible
class DjangoTemplateValidator:
    """
    Validate template code to be a valid Django template.

    This validators ensure that the template is syntactically correct. Additionally,
    it can enforce the presence of certain required template tags.
    """

    def __init__(self, required_template_tags: Optional[List[str]] = None):
        self.required_template_tags = required_template_tags

    def __call__(self, value: str) -> None:
        self.check_syntax_errors(value)
        self.check_required_tags(value)

    def check_required_tags(self, value):
        if not self.required_template_tags:
            return

        # since we already checked valid syntax we'll keep it simple and use string search
        #   instead of looking through the parsed structure
        for tag_name in self.required_template_tags:
            # note: the double {{ and }} are escapes for the format()
            variants = [
                "{{% {t} %}}".format(t=tag_name),
                "{{% {t}%}}".format(t=tag_name),
                "{{%{t} %}}".format(t=tag_name),
                "{{%{t}%}}".format(t=tag_name),
            ]
            for tag in variants:
                if tag in value:
                    break
            else:
                tag_str = "{{% {} %}}".format(tag_name)
                raise ValidationError(
                    _("Missing required template-tag {tag}").format(tag=tag_str),
                    code="invalid",
                )

    def check_syntax_errors(self, value):
        # code lifted from maykinmedia/mail-editor
        # https://github.com/maykinmedia/mail-editor/blob/e9ea1762af9a5c7ec0826876cb647dea444b95ba/mail_editor/mail_template.py#L28

        try:
            return Template(value)
        except TemplateSyntaxError as exc:
            error_tpl = """
                <p>{{ error }}</p>
                {% if source %}
                    {{ source|linenumbers|linebreaks }}
                {% endif %}
            """
            if hasattr(exc, "django_template_source"):
                source = exc.django_template_source[0].source
                pz = exc.django_template_source[1]
                highlighted_pz = ">>>>{0}<<<<".format(source[pz[0] : pz[1]])
                source = "{0}{1}{2}".format(
                    source[: pz[0]], highlighted_pz, source[pz[1] :]
                )
                _error = _("TemplateSyntaxError: {0}").format(exc.args[0])
            elif hasattr(exc, "template_debug"):
                _error = _("TemplateSyntaxError: {0}").format(
                    exc.template_debug.get("message")
                )
                source = "{}".format(exc.template_debug.get("during"))
            else:
                _error = exc
                source = None
            error = Template(error_tpl).render(
                Context({"error": _error, "source": source})
            )
            raise ValidationError(error, code="syntax_error")
