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
        "style": {
            # do we even have tokens for header? lets re-use footer for know
            "header": {
                "color": glom(design_token, "footer.color.value", default="black"),
                "background": glom(
                    design_token, "footer.background.value", default="orange"
                ),
            },
            "footer": {
                "color": glom(design_token, "footer.color.value", default="black"),
                "background": glom(
                    design_token, "footer.background.value", default="orange"
                ),
            },
            "layout": {
                "background": glom(
                    design_token, "layout.background.value", default="#e6e6e6"
                )
            },
        },
    }
    if config.logo:
        ctx["logo_url"] = build_absolute_uri(config.logo.url)

    return ctx
