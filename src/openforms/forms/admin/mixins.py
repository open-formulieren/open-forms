from openforms.config.models import GlobalConfiguration


class FormioConfigMixin:
    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        config = GlobalConfiguration.get_solo()
        context.update(
            {
                "required_default": config.form_fields_required_default,
            }
        )
        return super().render_change_form(request, context, add, change, form_url, obj)
