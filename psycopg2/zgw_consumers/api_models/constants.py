from django.utils.translation import gettext as _

from djchoices import ChoiceItem, DjangoChoices


class VertrouwelijkheidsAanduidingen(DjangoChoices):
    openbaar = ChoiceItem("openbaar", label="Openbaar")
    beperkt_openbaar = ChoiceItem("beperkt_openbaar", label="Beperkt openbaar")
    intern = ChoiceItem("intern", label="Intern")
    zaakvertrouwelijk = ChoiceItem("zaakvertrouwelijk", label="Zaakvertrouwelijk")
    vertrouwelijk = ChoiceItem("vertrouwelijk", label="Vertrouwelijk")
    confidentieel = ChoiceItem("confidentieel", label="Confidentieel")
    geheim = ChoiceItem("geheim", label="Geheim")
    zeer_geheim = ChoiceItem("zeer_geheim", label="Zeer geheim")


class RolTypes(DjangoChoices):
    natuurlijk_persoon = ChoiceItem("natuurlijk_persoon", "Natuurlijk persoon")
    niet_natuurlijk_persoon = ChoiceItem(
        "niet_natuurlijk_persoon", "Niet-natuurlijk persoon"
    )
    vestiging = ChoiceItem("vestiging", "Vestiging")
    organisatorische_eenheid = ChoiceItem(
        "organisatorische_eenheid", "Organisatorische eenheid"
    )
    medewerker = ChoiceItem("medewerker", "Medewerker")


class RolOmschrijving(DjangoChoices):
    adviseur = ChoiceItem(
        "adviseur",
        "Adviseur",
        description="Kennis in dienst stellen van de behandeling van (een deel van) een zaak.",
    )
    behandelaar = ChoiceItem(
        "behandelaar",
        "Behandelaar",
        description="De vakinhoudelijke behandeling doen van (een deel van) een zaak.",
    )
    belanghebbende = ChoiceItem(
        "belanghebbende",
        "Belanghebbende",
        description="Vanuit eigen en objectief belang rechtstreeks betrokken "
        "zijn bij de behandeling en/of de uitkomst van een zaak.",
    )
    beslisser = ChoiceItem(
        "beslisser",
        "Beslisser",
        description="Nemen van besluiten die voor de uitkomst van een zaak noodzakelijk zijn.",
    )
    initiator = ChoiceItem(
        "initiator",
        "Initiator",
        description="Aanleiding geven tot de start van een zaak ..",
    )
    klantcontacter = ChoiceItem(
        "klantcontacter",
        "Klantcontacter",
        description="Het eerste aanspreekpunt zijn voor vragen van burgers en bedrijven ..",
    )
    zaakcoordinator = ChoiceItem(
        "zaakcoordinator",
        "Zaakcoördinator",
        description="Er voor zorg dragen dat de behandeling van de zaak in samenhang "
        "uitgevoerd wordt conform de daarover gemaakte afspraken.",
    )
    medeinitiator = ChoiceItem("mede_initiator", "Mede-initiator", description="")


class VervalRedenen(DjangoChoices):
    tijdelijk = ChoiceItem("tijdelijk", "Besluit met tijdelijke werking")
    ingetrokken_overheid = ChoiceItem(
        "ingetrokken_overheid", "Besluit ingetrokken door overheid"
    )
    ingetrokken_belanghebbende = ChoiceItem(
        "ingetrokken_belanghebbende", "Besluit ingetrokken o.v.v. belanghebbende"
    )


class AardRelatieChoices(DjangoChoices):
    vervolg = ChoiceItem("vervolg", _("Vervolg"))
    bijdrage = ChoiceItem("bijdrage", _("Bijdrage"))
    onderwerp = ChoiceItem("onderwerp", _("Onderwerp"))
