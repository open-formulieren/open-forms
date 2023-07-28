from django.core.management import BaseCommand, CommandError

from openapi_parser import parse

from openforms.template import render_from_string

FILE_TEMPLATE = """
from django.db import models
from django.utils.translation import gettext_lazy as _

class Attributes(models.TextChoices):
    \"\"\"
    This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
    specs: {{ url }}
    schema: {{ schema }}
    command: {{ command }}
    \"\"\"

    {% for attribute in attributes %}{{ attribute.attribute_variable_name }} = "{{ attribute.attribute_value }}", _("{{ attribute.attribute_label }}")
    {% endfor %}
"""

# TODO features present in the old command (generate_prefill_from_spec)
# - Specify a service and then generate the attributes from the OAS of this service
# - Specify a path and then only generate the attributes for this path
# - If no path/schema are specified, print all paths and schemas in the OAS
# - Option to add '_embedded.' in paths for $refs
# - Keep track of the titles in addition to the properties names in the schema
OPTIONS = {
    "url": "URL to OAS specifications.",
    "schema": "Name of the API schema. The names can be found in the API schema in the path 'components > schemas'.",
}


class Command(BaseCommand):
    """Generate the attributes class (models.TextChoices) based on the OAS API specifications."""

    url = ""
    schema = ""
    parser = None

    def create_parser(self, prog_name, subcommand, **kwargs):
        self.parser = super().create_parser(prog_name, subcommand, **kwargs)
        return self.parser

    def add_arguments(self, parser):
        for option_name, option_help in OPTIONS.items():
            parser.add_argument(
                f"--{option_name}",
                action="store",
                type=str,
                help=option_help,
                default=None,
            )

    def get_specifications(self, options):
        if url := options.get("url"):
            self.url = url
            # The content types supported in the openapi3-parser are these:
            # https://github.com/manchenkoff/openapi3-parser/tree/master/src/openapi_parser/home/silvia/repositories/openapi3-parser/src/openapi_parser/enumeration.py
            # However, in the haal centraal OAS we find content types such as "application/hal+json". So with
            # strict_enum=False, the parser just checks that the content type is a string
            return parse(uri=url, strict_enum=False)

        raise CommandError("No URL to the OAS specifications was provided.")

    def get_attributes(self, property_schema):
        attributes = []
        if hasattr(property_schema.schema, "properties"):
            for schema_property in property_schema.schema.properties:
                nested_attributes = self.get_attributes(schema_property)
                attributes += [
                    [property_schema.name] + nested_attribute
                    for nested_attribute in nested_attributes
                ]
        else:
            attributes.append([property_schema.name])
        return attributes

    def get_schemas_attributes(self, oas_specifications, options):
        # In the specifications, the schemas are under the path "components > schemas"
        parsed_schemas = oas_specifications.schemas

        if requested_schema := options["schema"]:
            self.schema = requested_schema
            if requested_schema not in parsed_schemas:
                raise CommandError(
                    f'The given schema name "{requested_schema}" could not be found in the specifications'
                )

            return [
                self.get_attributes(schema_property)
                for schema_property in parsed_schemas[requested_schema].properties
            ]

        raise CommandError("No schema specified")

    def format_attributes(self, attributes, options):
        """Turn each attribute in ``{"attribute_variable_name": "bla_bla", "attribute_value": "bla.bla", "attribute_label": "Bla > Bla"}``"""
        formatted_attributes = []
        for nested_attributes in attributes:
            for attribute in nested_attributes:
                formatted_attributes.append(
                    {
                        "attribute_variable_name": (
                            "_".join(
                                [attribute_bit.lower() for attribute_bit in attribute]
                            )
                        ).lstrip("_"),
                        "attribute_value": ".".join(
                            [attribute_bit for attribute_bit in attribute]
                        ),
                        "attribute_label": " > ".join(
                            [attribute_bit.capitalize() for attribute_bit in attribute]
                        ),
                    }
                )
        return formatted_attributes

    def get_command(self, options):
        command_options = [
            f"--{option_key} {option_value}"
            for option_key, option_value in options.items()
            if option_key in OPTIONS
        ]
        return "{program_name} {program_options}".format(
            program_name=self.parser.prog, program_options=" ".join(command_options)
        )

    def handle(self, **options):
        oas_specifications = self.get_specifications(options)

        attributes = self.get_schemas_attributes(oas_specifications, options)

        formatted_attributes = self.format_attributes(attributes, options)

        rendered_template = render_from_string(
            FILE_TEMPLATE,
            context={
                "url": self.url,
                "schema": self.schema,
                "command": self.get_command(options),
                "attributes": formatted_attributes,
            },
            disable_autoescape=True,
        )

        self.stdout.write(rendered_template)
