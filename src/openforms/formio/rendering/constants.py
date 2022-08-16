from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class RenderConfigurationOptions(DjangoChoices):
    show_in_summary = ChoiceItem("showInSummary", _("Show in summary"))
    show_in_pdf = ChoiceItem("showInPDF", _("Show in PDF"))
    show_in_confirmation_email = ChoiceItem(
        "showInEmail", _("Show in confirmation email")
    )


RENDER_CONFIGURATION_CAMEL_TO_SNAKE = {
    RenderConfigurationOptions.show_in_confirmation_email: "show_in_email",
    RenderConfigurationOptions.show_in_pdf: "show_in_pdf",
    RenderConfigurationOptions.show_in_summary: "show_in_summary",
}
