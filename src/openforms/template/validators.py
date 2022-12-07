from django.core.exceptions import ValidationError
from django.template import Template, TemplateSyntaxError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _


@deconstructible
class DjangoTemplateValidator:
    """
    Validate template code to be a valid Django template.

    This validators ensure that the template is syntactically correct. Additionally,
    it can enforce the presence of certain required template tags.
    """

    def __init__(self, required_template_tags: list[str] | None = None):
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
            raise ValidationError(str(exc), code="syntax_error") from exc
