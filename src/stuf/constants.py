from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class EndpointSecurity(DjangoChoices):
    basicauth = ChoiceItem("basicauth", _("Basic authentication"))
    wss = ChoiceItem("wss", _("SOAP extension: WS-Security"))
    wss_basicauth = ChoiceItem("wss_basicauth", _("Both"))


class SOAPVersion(DjangoChoices):
    soap11 = ChoiceItem("1.1", "SOAP 1.1")
    soap12 = ChoiceItem("1.2", "SOAP 1.2")


class EndpointType(DjangoChoices):
    beantwoord_vraag = ChoiceItem("beantwoord_vraag", "BeantwoordVraag")
    vrije_berichten = ChoiceItem("vrije_berichten", "VrijeBerichten")
    ontvang_asynchroon = ChoiceItem("ontvang_asynchroon", "OntvangAsynchroon")


STUF_ZDS_EXPIRY_MINUTES = 5


SOAP_VERSION_CONTENT_TYPES = {
    SOAPVersion.soap11: "text/xml",
    SOAPVersion.soap12: "application/soap+xml",
}
