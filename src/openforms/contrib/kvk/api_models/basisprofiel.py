from typing import Literal, TypedDict

type JaNee = Literal["Ja", "Nee"]

# HAL links - if we fully type these, they should go in openforms.contrib.hal_client
type Links = list[dict]


class MaterieleRegistratie(TypedDict):
    datumAanvang: str
    datumEinde: str


class HandelsNaam(TypedDict):
    naam: str
    volgorde: int


class SBIActiviteit(TypedDict):
    sbiCode: str
    sbiOmschrijving: str
    indHoofdactiviteit: JaNee


class GeoData(TypedDict):
    addresseerbaarObjectId: str  # BAG ID
    nummerAanduidingId: str  # BAG ID
    gpsLatitude: float
    gpsLongitude: float
    rijksdriehoekX: float
    rijksdriehoekY: float
    rijksdriehoekZ: float


class Adres(TypedDict):
    type: str
    indAfgeschermd: JaNee
    volledigAdres: str
    straatnaam: str
    huisnummer: str
    huisnummerToevoeging: str
    huisletter: str
    toevoegingAdres: str
    postcode: str
    postbusnummer: int
    plaats: str
    straatHuisnummer: str
    postcodeWoonplaats: str
    regio: str
    land: str
    geoData: GeoData


class Vestiging(TypedDict):
    vestigingsnummer: str
    kvkNummer: str
    rsin: str
    indNonMailing: JaNee
    formeleRegistratiedatum: str
    materieleRegistratie: MaterieleRegistratie
    eersteHandelsnaam: str
    indHoofdvestiging: JaNee
    indCommercieleVestiging: JaNee
    voltijdWerkzamePersonen: int
    totaalWerkzamePersonen: int
    deeltijdWerkzamePersonen: int
    handelsnamen: list[HandelsNaam]
    adressen: list[Adres]
    websites: list[str]
    sbiActiviteiten: list[SBIActiviteit]
    links: Links


class Eigenaar(TypedDict):
    rsin: str
    rechtsvorm: str
    uitgebreideRechtsvorm: str
    adressen: list[Adres]
    websites: list[str]
    links: Links


class BasisProfielEmbedded(TypedDict):
    hoofdvestiging: Vestiging
    eigenaar: Eigenaar


class BasisProfiel(TypedDict):
    """
    Definition created from Swagger UI, API version 1.4.

    Docs: https://developers.kvk.nl/documentation/testing/swagger-basisprofiel-api
    """

    kvkNummer: str
    indNonMailing: str
    naam: str
    formeleRegistratiedatum: str
    materieleRegistratie: MaterieleRegistratie
    totaalWerkzamePersonen: int
    statutaireNaam: str
    handelsnamen: list[HandelsNaam]
    sbiActiviteiten: list[SBIActiviteit]
    links: Links
    _embedded: BasisProfielEmbedded
