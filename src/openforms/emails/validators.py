import re
from typing import List, Optional

from django.core.exceptions import ValidationError
from django.template import Context, Template, TemplateSyntaxError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _


@deconstructible
class DjangoTemplateValidator:
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
            # note: the double {{ and }} are escapes for the formatting
            exp = "{{% *{} *%}}".format(tag_name)
            if not re.search(exp, value):
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
