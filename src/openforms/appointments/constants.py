from djchoices import ChoiceItem, DjangoChoices


class AppointmentsConfigPaths(DjangoChoices):
    jcc = ChoiceItem("openforms.appointments.contrib.jcc.models.JccConfig", "Jcc")
    qmatic = ChoiceItem(
        "openforms.appointments.contrib.qmatic.models.QmaticConfig", "Qmatic"
    )


class AppointmentDetailsStatus(DjangoChoices):
    success = ChoiceItem("success", "Success")
    missing_info = ChoiceItem(
        "missing_info",
        "Submission does not contain all the info needed to make an appointment",
    )
    failed = ChoiceItem("failed", "Failed")
    cancelled = ChoiceItem("cancelled", "Cancelled")
