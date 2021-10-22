from django.core.exceptions import ValidationError
from django.test import TestCase

from openforms.emails.validators import DjangoTemplateValidator


class DjangoTemplateValidatorTest(TestCase):
    def test_template_syntax(self):
        validator = DjangoTemplateValidator()

        # valid
        validator("")
        validator(" \n \n ")
        validator("aa")
        validator("{{ aa }}")
        validator(
            '{% load i18n %}<p>{% trans "foo" %} {% if aa %}{{ aa.bb.cc }}{% endif %}</p>'
        )

        # note: in-complete tags are acceptable to the template language
        validator("{{ aa }")
        validator("{% foo %")

        # syntax errors
        with self.assertRaisesRegex(ValidationError, "Could not parse the remainder:"):
            validator("{{{}}}")

        with self.assertRaisesRegex(
            ValidationError, "Unexpected end of expression in if tag."
        ):
            validator("{% if %}")

        with self.assertRaisesRegex(ValidationError, "Invalid block tag on line 1:"):
            validator("{% foo %}")

        with self.assertRaisesRegex(ValidationError, "Invalid block tag on line 1:"):
            validator("{% $$ %}")

    def test_required_tags(self):
        validator = DjangoTemplateValidator(required_template_tags=["csrf_token"])

        validator("{% csrf_token %}")
        validator("{%csrf_token%}")
        validator("{% load i18n %} aa {% csrf_token %} {{ aa.bb.cc }}")

        with self.assertRaisesRegex(
            ValidationError, "Missing required template-tag \{% csrf_token %}"
        ):
            validator("")

        with self.assertRaisesRegex(
            ValidationError, "Missing required template-tag \{% csrf_token %}"
        ):
            validator("{% load i18n %} aa {{ aa.bb.cc }}")
