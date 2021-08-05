from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://developers.kvk.nl/cms/api/uploads/api_zoeken_80071c75c9.yaml
    schema:  ResultaatItem
    command: manage.py generate_prefill_from_spec --schema ResultaatItem --url https://developers.kvk.nl/cms/api/uploads/api_zoeken_80071c75c9.yaml
    """

    handelsnaam = ChoiceItem("handelsnaam", _("handelsnaam"))
    kvkNummer = ChoiceItem("kvkNummer", _("kvkNummer"))
    plaats = ChoiceItem("plaats", _("plaats"))
    rsin = ChoiceItem("rsin", _("rsin"))
    straatnaam = ChoiceItem("straatnaam", _("straatnaam"))
    type = ChoiceItem("type", _("type"))
    vestigingsnummer = ChoiceItem("vestigingsnummer", _("vestigingsnummer"))
