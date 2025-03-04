from openforms.formio.typing import Component
from openforms.utils.sanitizer import sanitize_html_content


def sanitize_component(component: Component):
    """
    Sanitize content of any form component.

    The tooltip, description and label content will be replaced with a sanitized version.
    All tags and attributes that aren't explicitly allowed, are removed from the
    component content.

    :arg component: the component data.
    """
    if "tooltip" in component:
        component["tooltip"] = sanitize_html_content(component["tooltip"])
    if "description" in component:
        component["description"] = sanitize_html_content(component["description"])
    if "label" in component:
        component["label"] = sanitize_html_content(component["label"])
