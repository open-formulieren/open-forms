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
        "style": _get_design_token_values(design_tokens),
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
            "color": glom(token, "page-header.color.value", default="black"),
            "background": glom(
                token, "page-header.background.value", default="#2980b9"
            ),
        },
        "logo": {
            "height": glom(token, "logo-header.height.value", default="auto"),
            "width": glom(token, "logo-header.width.value", default="auto"),
        },
        "footer": {
            "color": glom(token, "footer.color.value", default="black"),
            "background": glom(token, "footer.background.value", default="#2980b9"),
        },
        "layout": {
            "background": glom(token, "layout.background.value", default="#e6e6e6")
        },
    }
