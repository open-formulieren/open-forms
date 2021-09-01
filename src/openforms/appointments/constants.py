from djchoices import ChoiceItem, DjangoChoices


class AppointmentsConfigPaths(DjangoChoices):
    jcc = ChoiceItem("openforms.appointments.contrib.jcc.models.JccConfig", "Jcc")
    qmatic = ChoiceItem(
        "openforms.appointments.contrib.qmatic.models.QmaticConfig", "Qmatic"
    )
