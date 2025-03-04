import bleach

from openforms.formio.typing import Component

ALLOWED_HTML_TAGS = (
    # Basic text tags
    "a",
    "b",
    "br",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "i",
    "p",
    "s",
    "strong",
    "sup",
    "u",
    # Lists
    "li",
    "ol",
    "ul",
)

ALLOWED_HTML_ATTRIBUTES = {"a": ("href", "target", "rel")}


def sanitize_form_component(component: Component) -> Component:
    """
    Sanitize content of any form component.

    The tooltip, description and label content will be replaced with a sanitized version.
    All tags and attributes that aren't explicitly allowed, are removed from the
    component content.

    :arg component: the component data.
    """
    component["tooltip"] = sanitize_html_content(component.get("tooltip", ""))
    component["description"] = sanitize_html_content(component.get("description", ""))
    component["label"] = sanitize_html_content(component["label"])


def sanitize_html_content(html_content: str) -> str:
    """
    Defuse html string.

    The provided string is replaced by a html sanitized version. All tags and attributes
    that aren't explicitly allowed, are removed from the SVG content.

    :arg html_content: the html string to sanitize.
    """
    return bleach.clean(
        html_content,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )
