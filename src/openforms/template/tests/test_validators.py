from django.core.exceptions import ValidationError
from django.template import engines
from django.test import SimpleTestCase, override_settings
from django.utils.translation import gettext as _

from ..validators import DjangoTemplateValidator

# Grab the first template backend from settings.TEMPLATES, which at the time of writing
# is/should be the regular vanilla Django templates backend.
#
# If this assertion fails, it'll most likely be because of changing the template engine
# to Jinja2 or something else - check your TEMPLATES setting and adapt the index below
# as needed.
django_backend = engines.all()[0]
assert (
    type(django_backend).__name__ == "DjangoTemplates"
), "Expected the backend to be a plain (non-sandboxed) Django templates backend."


class DjangoTemplateValidatorTest(SimpleTestCase):
    def test_template_syntax(self):
        validator = DjangoTemplateValidator(backend=f"{__name__}.django_backend")

        valid = [
            "",
            " \n \n ",
            "aa",
            "{{ aa }}",
            '{% load i18n %}<p>{% trans "foo" %} {% if aa %}{{ aa.bb.cc }}{% endif %}</p>',
            # note: in-complete tags are acceptable to the template language
            "{{ aa }",
            "{% foo %",
        ]
        for text in valid:
            with self.subTest(f"valid: {text}"):
                validator(text)

        invalid = [
            ("{{{}}}", "Could not parse the remainder:"),
            ("{% if %}", "Unexpected end of expression in if tag."),
            ("{% foo %}", "Invalid block tag on line 1:"),
            ("{% $$ %}", "Invalid block tag on line 1:"),
        ]
        for text, message in invalid:
            with self.subTest(f"invalid: {text}"):
                with self.assertRaisesRegex(ValidationError, message):
                    validator(text)

    def test_required_tags(self):
        validator = DjangoTemplateValidator(
            required_template_tags=["csrf_token"],
            backend=f"{__name__}.django_backend",
        )

        valid = [
            "{% csrf_token %}",
            "{%csrf_token %}",
            "{% csrf_token%}",
            "{%csrf_token%}",
            "{% load i18n %} aa {% csrf_token %} {{ aa.bb.cc }}",
        ]
        for text in valid:
            with self.subTest(f"valid: {text}"):
                validator(text)

        invalid = [
            (
                "",
                _("Missing required template-tag {tag}").format(
                    tag=r"\{% csrf_token %}"
                ),
            ),
            (
                "{% load i18n %} aa {{ aa.bb.cc }}",
                _("Missing required template-tag {tag}").format(
                    tag=r"\{% csrf_token %}"
                ),
            ),
        ]
        for text, message in invalid:
            with self.subTest(f"invalid: {text}"):
                with self.assertRaisesRegex(ValidationError, message):
                    validator(text)

    @override_settings(LANGUAGE_CODE="en")
    def test_validation_error_no_html(self):
        """
        Validation errors cannot contain HTML if they're used in API endpoints.

        Discovered via #2418 - while the markup works nicely in the Django admin,
        DRF cannot handle the templated out validation error. ErrorDetail is a str
        subclass, and essentially discards the SafeString contextual information.
        Additionally, it's hard to selectively allow HTML in the frontend code without
        increasing XSS risks.
        """
        validator = DjangoTemplateValidator(backend=f"{__name__}.django_backend")

        with self.assertRaisesMessage(
            ValidationError,
            "Invalid block tag on line 1: 'bad-tag'. Did you forget to register "
            "or load this tag?",
        ):
            validator("{% bad-tag %}")
