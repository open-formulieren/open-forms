from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.utils.deconstruct import deconstructible
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _

from . import parse


@deconstructible
class DjangoTemplateValidator:
    """
    Validate template code to be a valid Django template.

    This validators ensure that the template is syntactically correct. Additionally,
    it can enforce the presence of certain required template tags.
    """

    def __init__(
        self,
        required_template_tags: list[str] | None = None,
        backend: str = "openforms.template.sandbox_backend",
    ):
        self.required_template_tags = required_template_tags
        self.backend = backend

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
                f"{{% {tag_name} %}}",
                f"{{% {tag_name}%}}",
                f"{{%{tag_name} %}}",
                f"{{%{tag_name}%}}",
            ]
            for tag in variants:
                if tag in value:
                    break
            else:
                tag_str = f"{{% {tag_name} %}}"
                raise ValidationError(
                    _("Missing required template-tag {tag}").format(tag=tag_str),
                    code="invalid",
                )

    def check_syntax_errors(self, value):
        backend = import_string(self.backend)
        try:
            parse(value, backend=backend)
        except TemplateSyntaxError as exc:
            raise ValidationError(str(exc), code="syntax_error") from exc
