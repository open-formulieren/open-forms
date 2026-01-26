from django.test import SimpleTestCase

from .. import extract_variables_used


class ExtractVariablesTests(SimpleTestCase):
    def test_extract_vars_without_filters(self):
        source = """
        I have {{ foo }} {{bar}}s, but they don't {{ baz}}.
        """

        variable_names = set(extract_variables_used(source))

        self.assertEqual(variable_names, {"foo", "bar", "baz"})

    def test_extract_vars_with_filters(self):
        source = """
        This is a {{ foo|default:'nope' }}!
        """

        variable_names = set(extract_variables_used(source))

        self.assertEqual(variable_names, {"foo"})

    def test_vars_nested_in_loop(self):
        source = """
        {% for someVar in 'abcd' %}
            It is {{ someVar }}
        {% endfor %}
        """

        variable_names = set(extract_variables_used(source))

        self.assertEqual(variable_names, {"someVar"})

    def test_var_in_for_loop(self):
        source = """
        {% for attachment in attachments %}
            It is {{ attachment }}
        {% endfor %}
        """

        variable_names = set(extract_variables_used(source))

        self.assertEqual(variable_names, {"attachment", "attachments"})

    def test_var_in_if_statement(self):
        source = """
        {% if someVarInIf %}
            {{otherVar}}
        {% elif otherVarInIf == 'asdf' %}
            {{yetAnotherVar}}
        {% elif 'foo' == finalVarInIf %}
            {{reallyLastVarIPromise}}
        {% endif %}
        """

        variable_names = set(extract_variables_used(source))

        self.assertEqual(
            variable_names,
            {
                "otherVar",
                "otherVarInIf",
                "someVarInIf",
                "yetAnotherVar",
                "finalVarInIf",
                "reallyLastVarIPromise",
            },
        )
