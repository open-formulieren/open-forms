from django.utils.safestring import mark_safe

from glom import glom

from openforms.config.models import GlobalConfiguration
from openforms.utils.urls import build_absolute_uri


def get_wrapper_context(html_content=""):
    config = GlobalConfiguration.get_solo()
    design_token = config.design_token_values or {}
    ctx = {
        "content": mark_safe(html_content),
        "main_website_url": config.main_website,
        "style": _get_design_token_values(design_token),
    }
    if config.logo:
        ctx["logo_url"] = build_absolute_uri(config.logo.url)

    return ctx


def _get_design_token_values(tokens):
    """
    convert and apply defaults for use in template
    """
    return {
        "header": {
            "color": glom(tokens, "page-header.color.value", default="#000000"),
            "background": glom(
                tokens, "page-header.background.value", default="#ffffff"
            ),
        },
        "logo": {
            # Setting height to a default of 50 obtaines the same result on the 
            # website that uses flexbox shrink, to size the logo to it's minimum
            # size.
            "height": glom(tokens, "logo-header.height.value", default="50"),
            "width": glom(tokens, "logo-header.width.value", default="auto"),
        },
        "footer": {
            "color": glom(tokens, "footer.color.value", default="#ffffff"),
            "background": glom(tokens, "footer.background.value", default="#2980b9"),
        },
        "layout": {
            "background": glom(tokens, "layout.background.value", default="#e6e6e6")
        },
    }
