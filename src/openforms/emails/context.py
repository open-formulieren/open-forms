from django.utils.safestring import mark_safe

from glom import glom

from openforms.config.models import GlobalConfiguration
from openforms.utils.urls import build_absolute_uri


def get_wrapper_context(html_content=""):
    config = GlobalConfiguration.get_solo()
    design_tokens = config.design_token_values or {}
    ctx = {
        "content": mark_safe(html_content),
        "main_website_url": config.main_website,
        "style": _get_design_token_values(design_tokens),
    }
    if config.logo:
        ctx["logo_url"] = build_absolute_uri(config.logo.url)

    return ctx


def _filter(value: str) -> str:
    if value.isnumeric():
        return value
    elif value.endswith("px"):
        return value.strip("px")
    else:
        return ""


def _get_design_token_values(tokens):
    """
    convert and apply defaults for use in email template

    Dimension values for design tokens specified as CSS or as attributes
    of HTML tags need to be handled differently because of issues with the
    desktop client of MS Outlook. The former are used as passed in by the
    user; the latter are filtered via ``filter_design_token_values``.

    TODO: convert to use style-dict assets merged with database tokens
    TODO: figure out how to use the remote stylesheet for this
    """
    height = glom(tokens, "header-logo.height.value", default="50px")
    width = glom(tokens, "header-logo.width.value", default="auto")
    height_attr = _filter(height)
    width_attr = _filter(width)

    return {
        "header": {
            "fg": glom(tokens, "page-header.fg.value", default="#000000"),
            "bg": glom(tokens, "page-header.bg.value", default="#ffffff"),
        },
        "logo": {
            # Setting height to a default of 50 obtaines the same result on the
            # website that uses flexbox shrink, to size the logo to it's minimum
            # size.
            "height": height,
            "width": width,
            # attr values are for specifying dimensions as attributes of the
            # HTML image tag
            "height_attr": height_attr,
            "width_attr": width_attr,
        },
        "footer": {
            "fg": glom(tokens, "page-footer.fg.value", default="#ffffff"),
            "bg": glom(tokens, "page-footer.bg.value", default="#2980b9"),
        },
        "layout": {"bg": glom(tokens, "layout.bg.value", default="#e6e6e6")},
    }
