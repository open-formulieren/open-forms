from django.views.generic import TemplateView

from openforms.emails.context import get_wrapper_context


class EmailWrapperTestView(TemplateView):
    template_name = "emails/wrapper.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx.update(get_wrapper_context("<b>content goes here</b>"))
        ctx.update(kwargs)
        return ctx
