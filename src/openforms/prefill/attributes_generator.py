from collections.abc import Iterator
from dataclasses import dataclass

from openapi_parser import parse
from openapi_parser.specification import Object, Property, Specification

from openforms.template import render_from_string


class AttributeGeneratorException(Exception):
    pass


FILE_TEMPLATE = """
from django.db import models
from django.utils.translation import gettext_lazy as _

class Attributes(models.TextChoices):
    \"\"\"
    This code was (at some point) generated from the management command below. Names and labels are in Dutch if the spec was Dutch
    spec: {{ uri }}
    schema: {{ schema }}
    command: {{ command }}
    \"\"\"

    {% for attribute in attributes %}{{ attribute.variable_name }} = "{{ attribute.value }}", _("{{ attribute.label }}")
    {% endfor %}
"""


@dataclass()
class Attribute:
    """
    Prepare attributes for code generation.

    Each attribute is prepared by:

    * using snake_case to create valid variable names/identifiers
    * creating a string value with periods as path separators
    * capitalize each part for the human-readable label
    """

    parts: list[str]

    @property
    def variable_name(self) -> str:
        return "_".join(part.lower() for part in self.parts).lstrip("_")

    @property
    def value(self) -> str:
        return ".".join(self.parts)

    @property
    def label(self) -> str:
        return " > ".join(part.capitalize() for part in self.parts)


def get_schema_attributes(
    oas_specification: Specification, schema_name: str
) -> Iterator[Attribute]:
    if (schema := oas_specification.schemas.get(schema_name)) is None:
        raise AttributeGeneratorException(
            f'The given schema name "{schema_name}" could not be found in the specifications'
        )

    assert isinstance(schema, Object), f"Expected an object schema, got {type(schema)}."
    for schema_property in schema.properties:
        yield from get_property_attributes(schema_property)


def get_property_attributes(
    property: Property, prefix: list[str] | None = None
) -> Iterator[Attribute]:
    if isinstance(property.schema, Object):
        nested_prefix = prefix + [property.name] if prefix else [property.name]
        for nested in property.schema.properties:
            yield from get_property_attributes(nested, prefix=nested_prefix)
    else:
        parts = (prefix or []) + [property.name]
        yield Attribute(parts)


@dataclass
class OpenApi3AttributesGenerator:
    """Generate the attributes from OAS specification

    TODO features present in the generate_prefill_from_spec command

    * Specify a service and then generate the attributes from the OAS of this service
    * Specify a path and then only generate the attributes for this path
    * If no path/schema are specified, print all paths and schemas in the OAS
    * Option to add '_embedded.' in paths for $refs

    Additional features that could be good

    * Keep track of the titles in addition to the properties names in the schema
    """

    uri: str = ""
    """
    The URL of the OAS specification
    """
    schema: str = ""
    """
    The name of the schema in the specification from which to generate the attributes
    """
    command: str = ""
    """
    The command used to generate the attributes
    """

    def generate_attributes(self) -> str:
        oas_specification = self._load_specification()
        attributes = get_schema_attributes(oas_specification, self.schema)
        return render_from_string(
            FILE_TEMPLATE,
            context={
                "uri": self.uri,
                "schema": self.schema,
                "attributes": attributes,
                "command": self.command,
            },
            disable_autoescape=True,
        )

    def _load_specification(self) -> Specification:
        if not self.uri:
            raise AttributeGeneratorException("No OAS specification URI was provided.")

        # The content types supported in the openapi3-parser are these:
        # https://github.com/manchenkoff/openapi3-parser/blob/master/src/openapi_parser/enumeration.py#L97
        # However, in the haal centraal OAS we find content types such as "application/hal+json". So with
        # strict_enum=False, the parser just checks that the content type is a string
        return parse(uri=self.uri, strict_enum=False)
