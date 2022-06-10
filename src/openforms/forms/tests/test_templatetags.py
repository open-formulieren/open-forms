from django.template import Context, Template
from django.test import SimpleTestCase


class SpacerTagTests(SimpleTestCase):
    def test_render_spacers(self):
        template = Template(
            """
            {% load forms_admin_list %}
            {% render_spacers 3 classname="foo" %}
        """
        )

        rendered = template.render(Context())

        self.assertInHTML('<span class="foo"></span>', rendered, count=3)

    def test_render_empty(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):

                template = Template(
                    """
                    {% load forms_admin_list %}
                    {% render_spacers amount %}
                """
                )

                rendered = template.render(Context({"amount": amount})).strip()

                self.assertEqual(rendered, "")
