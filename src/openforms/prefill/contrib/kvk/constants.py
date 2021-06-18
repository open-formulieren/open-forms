from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    """
    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch

    spec:    https://developers.kvk.nl/files/swagger/kvkapiprofileoas3.yml
    schema:  CompanyExtendedV2
    command: manage.py generate_prefill_from_spec --schema CompanyExtendedV2 --url https://developers.kvk.nl/files/swagger/kvkapiprofileoas3.yml
    """

    # TODO support array elements

    addresses_i_bagId = ChoiceItem("addresses[].bagId", _("addresses > [] > bagId"))
    addresses_i_city = ChoiceItem("addresses[].city", _("addresses > [] > city"))
    addresses_i_country = ChoiceItem(
        "addresses[].country", _("addresses > [] > country")
    )
    addresses_i_gpsLatitude = ChoiceItem(
        "addresses[].gpsLatitude", _("addresses > [] > gpsLatitude")
    )
    addresses_i_gpsLongitude = ChoiceItem(
        "addresses[].gpsLongitude", _("addresses > [] > gpsLongitude")
    )
    addresses_i_houseNumber = ChoiceItem(
        "addresses[].houseNumber", _("addresses > [] > houseNumber")
    )
    addresses_i_houseNumberAddition = ChoiceItem(
        "addresses[].houseNumberAddition", _("addresses > [] > houseNumberAddition")
    )
    addresses_i_postalCode = ChoiceItem(
        "addresses[].postalCode", _("addresses > [] > postalCode")
    )
    addresses_i_rijksdriehoekX = ChoiceItem(
        "addresses[].rijksdriehoekX", _("addresses > [] > rijksdriehoekX")
    )
    addresses_i_rijksdriehoekY = ChoiceItem(
        "addresses[].rijksdriehoekY", _("addresses > [] > rijksdriehoekY")
    )
    addresses_i_rijksdriehoekZ = ChoiceItem(
        "addresses[].rijksdriehoekZ", _("addresses > [] > rijksdriehoekZ")
    )
    addresses_i_street = ChoiceItem("addresses[].street", _("addresses > [] > street"))
    addresses_i_type = ChoiceItem("addresses[].type", _("addresses > [] > type"))
    branchNumber = ChoiceItem("branchNumber", _("branchNumber"))
    businessActivities_i_isMainSbi = ChoiceItem(
        "businessActivities[].isMainSbi", _("businessActivities > [] > isMainSbi")
    )
    businessActivities_i_sbiCode = ChoiceItem(
        "businessActivities[].sbiCode", _("businessActivities > [] > sbiCode")
    )
    businessActivities_i_sbiCodeDescription = ChoiceItem(
        "businessActivities[].sbiCodeDescription",
        _("businessActivities > [] > sbiCodeDescription"),
    )
    deregistrationDate = ChoiceItem("deregistrationDate", _("deregistrationDate"))
    employees = ChoiceItem("employees", _("employees"))
    foundationDate = ChoiceItem("foundationDate", _("foundationDate"))
    hasCommercialActivities = ChoiceItem(
        "hasCommercialActivities", _("hasCommercialActivities")
    )
    hasEntryInBusinessRegister = ChoiceItem(
        "hasEntryInBusinessRegister", _("hasEntryInBusinessRegister")
    )
    hasNonMailingIndication = ChoiceItem(
        "hasNonMailingIndication", _("hasNonMailingIndication")
    )
    isBranch = ChoiceItem("isBranch", _("isBranch"))
    isLegalPerson = ChoiceItem("isLegalPerson", _("isLegalPerson"))
    isMainBranch = ChoiceItem("isMainBranch", _("isMainBranch"))
    kvkNumber = ChoiceItem("kvkNumber", _("kvkNumber"))
    legalForm = ChoiceItem("legalForm", _("legalForm"))
    registrationDate = ChoiceItem("registrationDate", _("registrationDate"))
    rsin = ChoiceItem("rsin", _("rsin"))
    tradeNames_businessName = ChoiceItem(
        "tradeNames.businessName", _("tradeNames > businessName")
    )
    tradeNames_currentNames_i = ChoiceItem(
        "tradeNames.currentNames[]", _("tradeNames > currentNames > []")
    )
    tradeNames_currentStatutoryNames_i = ChoiceItem(
        "tradeNames.currentStatutoryNames[]",
        _("tradeNames > currentStatutoryNames > []"),
    )
    tradeNames_currentTradeNames_i = ChoiceItem(
        "tradeNames.currentTradeNames[]", _("tradeNames > currentTradeNames > []")
    )
    tradeNames_formerNames_i = ChoiceItem(
        "tradeNames.formerNames[]", _("tradeNames > formerNames > []")
    )
    tradeNames_formerStatutoryNames_i = ChoiceItem(
        "tradeNames.formerStatutoryNames[]", _("tradeNames > formerStatutoryNames > []")
    )
    tradeNames_formerTradeNames_i = ChoiceItem(
        "tradeNames.formerTradeNames[]", _("tradeNames > formerTradeNames > []")
    )
    tradeNames_shortBusinessName = ChoiceItem(
        "tradeNames.shortBusinessName", _("tradeNames > shortBusinessName")
    )
    websites_i = ChoiceItem("websites[]", _("websites > []"))
