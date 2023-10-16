from dataclasses import dataclass
from pathlib import Path

WSDLS = Path(__file__).parent.resolve() / "wsdls"


@dataclass
class Service:
    name: str
    wsdl: str
    operations: list[str]

    @property
    def wsdl_path(self) -> str:
        return str(WSDLS / self.wsdl)


SERVICES: dict[str, Service] = {
    service.name: service
    for service in [
        Service(
            name="BRPDossierPersoonGSD",
            wsdl="BRPDossierPersoonGSD-v0200-b02/Diensten/BRPDossierPersoonGSD/v0200-b02/BRPDossierPersoonGSD.wsdl",
            operations=["AanvraagPersoon"],
        ),
        Service(
            name="Bijstandsregelingen",
            wsdl="Bijstandsregelingen-v0500-b04/Diensten/Bijstandsregelingen/v0500-b04/Bijstandsregelingen.wsdl",
            operations=["BijstandsregelingenInfo"],
        ),
        Service(
            name="DUODossierPersoonGSD",
            wsdl="DUODossierPersoonGSD-v0300-b01/Diensten/DUODossierPersoonGSD/v0300-b01/DUODossierPersoonGSD.wsdl",
            operations=["DUOPersoonsInfo"],
        ),
        Service(
            name="DUODossierStudiefinancieringGSD",
            wsdl="DUODossierStudiefinancieringGSD-v0200-b01/Diensten/DUODossierStudiefinancieringGSD/v0200-b01/DUODossierStudiefinancieringGSD.wsdl",
            operations=["DUOStudiefinancieringInfo"],
        ),
        Service(
            name="GSDDossierReintegratie",
            wsdl="GSDDossierReintegratie-v0200-b04/Diensten/GSDDossierReintegratie/v0200-b04/GSDDossierReintegratie.wsdl",
            operations=["GSDReintegratieInfo"],
        ),
        Service(
            name="IBVerwijsindex",
            wsdl="IBVerwijsindex-v0300-b01/Diensten/IBVerwijsindex/v0300-b01/IBVerwijsindex.wsdl",
            operations=[
                # "IBVerwijsindex",
                # Has this signature:
                # IBVerwijsindex(Burgerservicenr: ns1:Burgerservicenr
                #               , ClusteringIb: {CdClusteringIb: ns0:CdClusteringIb, IndDkd: ns1:StdIndJN}[],
                #               , Bron: {CdKolomSuwi: ns1:CdKolomSuwi, CdPartijSuwi: ns1:CdPartijSuwi, CdVestigingSuwi: ns1:CdVestigingSuwi}
                #               ) -> Acknowledgement: ns0:Acknowledgement, FWI: ns2:FWI
            ],
        ),
        Service(
            name="KadasterDossierGSD",
            wsdl="KadasterDossierGSD-v0300-b02/Diensten/KadasterDossierGSD/v0300-b02/KadasterDossierGSD.wsdl",
            operations=[
                # "ObjectInfoKadastraleAanduiding",
                # ObjectInfoKadastraleAanduiding(CdKadastraleGemeente: ns1:CdKadastraleGemeente
                #                               , KadastraleGemeentenaam: ns1:NaamAdresNederlandAN40
                #                               , KadastraleSectie: ns0:KadastraleSectie
                #                               , KadastraalPerceelnr: ns0:KadastraalPerceelnr
                #                               , VolgnrKadastraalAppartementsrecht: ns0:VolgnrKadAppartementsrecht
                #                               ) -> ...
                # "ObjectInfoLocatieOZ",
                # ObjectInfoLocatieOZ(Postcd: ns1:Postcd
                #                    , Huisnr: ns1:NummerAdresNederlandN5
                #                    , Huisnrtoevoeging: ns1:NummerAdresNederlandAN6
                #                    , Huisletter: ns1:NummerAdresNederlandAN1
                #                    ) -> ...
                "PersoonsInfo",
            ],
        ),
        Service(
            name="RDWDossierDigitaleDiensten",
            wsdl="RDWDossierDigitaleDiensten-v0200-b01/Diensten/RDWDossierDigitaleDiensten/v0200-b01/RDWDossierDigitaleDiensten.wsdl",
            operations=[
                # "KentekenInfo",
                # KentekenInfo(Burgerservicenr: ns1:Burgerservicenr, KentekenVoertuig: ns1:NummerAN6) -> ...
                "VoertuigbezitInfoPersoon",
            ],
        ),
        Service(
            name="RDWDossierGSD",
            wsdl="RDWDossierGSD-v0200-b02/Diensten/RDWDossierGSD/v0200-b02/RDWDossierGSD.wsdl",
            operations=[
                # "KentekenInfo",
                # KentekenInfo(KentekenVoertuig: ns1:NummerAN6
                #             , PeildatAansprakelijkheid: ns1:Datum
                #             , PeiltijdAansprakelijkheid: ns1:Tijdstip
                #             ) -> ...
                # "VoertuigbezitInfoOrg",
                # VoertuigbezitInfoOrg(InschrijvingsnrKvK: ns1:InschrijvingsnrKvK
                #                     , VestigingsnrHandelsregister: ns0:VestigingsnrHandelsregister
                #                     , DatBPeilperiodeAansprakelijkheid: ns1:Datum
                #                     , DatEPeilperiodeAansprakelijkheid: ns1:Datum
                #                     ) -> ...
                # "VoertuigbezitInfoPersoon",
                # VoertuigbezitInfoPersoon(({Burgerservicenr: ns1:Burgerservicenr}
                #                          | {Geboortedat: ns1:Datum, SignificantDeelVanDeAchternaam: ns1:NaamPersoonA200, Voorletters: ns1:Voorletters}
                #                          | {Postcd: ns1:Postcd, Huisnr: ns1:NummerAdresNederlandN5}
                #                          )
                #                         , DatBPeilperiodeAansprakelijkheid: ns1:Datum
                #                         , DatEPeilperiodeAansprakelijkheid: ns1:Datum
                #                         ) -> ...
            ],
        ),
        Service(
            name="SVBDossierPersoonGSD",
            wsdl="SVBDossierPersoonGSD-v0200-b01/Diensten/SVBDossierPersoonGSD/v0200-b01/SVBDossierPersoonGSD.wsdl",
            operations=["SVBPersoonsInfo"],
        ),
        Service(
            name="UWVDossierAanvraagUitkeringStatusGSD",
            wsdl="UWVDossierAanvraagUitkeringStatusGSD-v0200-b01/Diensten/UWVDossierAanvraagUitkeringStatusGSD/v0200-b01/UWVDossierAanvraagUitkeringStatusGSD.wsdl",
            operations=["UWVAanvraagUitkeringStatusInfo"],
        ),
        Service(
            name="UWVDossierInkomstenGSD",
            wsdl="UWVDossierInkomstenGSD-v0200-b02/Diensten/UWVDossierInkomstenGSD/v0200-b02/UWVDossierInkomstenGSD.wsdl",
            operations=[
                # "UWVPersoonsIkvInfo",
                # UWVPersoonsIkvInfo(Burgerservicenr: ns1:Burgerservicenr
                #                   , PeriodeGegevensvraagIko: {DatBPeriode: ns1:Datum, DatEPeriode: ns1:Datum}
                #                   ) -> ...
            ],
        ),
        Service(
            name="UWVDossierInkomstenGSDDigitaleDiensten",
            wsdl="UWVDossierInkomstenGSDDigitaleDiensten-v0200-b01/Diensten/UWVDossierInkomstenGSDDigitaleDiensten/v0200-b01/UWVDossierInkomstenGSDDigitaleDiensten.wsdl",
            operations=[
                # "UWVPersoonsIkvInfo",
                # UWVPersoonsIkvInfo(Burgerservicenr: ns1:Burgerservicenr
                #                    , PeriodeGegevensvraagIko: {DatBPeriode: ns1:Datum, DatEPeriode: ns1:Datum}
                #                    ) -> ...
            ],
        ),
        Service(
            name="UWVDossierQuotumArbeidsbeperktenGSD",
            wsdl="UWVDossierQuotumArbeidsbeperktenGSD-v0300-b01/Diensten/UWVDossierQuotumArbeidsbeperktenGSD/v0300-b01/UWVDossierQuotumArbeidsbeperktenGSD.wsdl",
            operations=["UWVPersoonsArbeidsbeperktenInfo"],
        ),
        Service(
            name="UWVDossierWerknemersverzekeringenGSD",
            wsdl="UWVDossierWerknemersverzekeringenGSD-v0200-b01/Diensten/UWVDossierWerknemersverzekeringenGSD/v0200-b01/UWVDossierWerknemersverzekeringenGSD.wsdl",
            operations=["UWVPersoonsWvInfo"],
        ),
        Service(
            name="UWVDossierWerknemersverzekeringenGSDDigitaleDiensten",
            wsdl="UWVDossierWerknemersverzekeringenGSDDigitaleDiensten-v0200-b01/Diensten/UWVDossierWerknemersverzekeringenGSDDigitaleDiensten/v0200-b01/UWVDossierWerknemersverzekeringenGSDDigitaleDiensten.wsdl",
            operations=["UWVPersoonsWvInfo"],
        ),
        Service(
            name="UWVWbDossierPersoonGSD",
            wsdl="UWVWbDossierPersoonGSD-v0200-b01/Diensten/UWVWbDossierPersoonGSD/v0200-b01/UWVWbDossierPersoonGSD.wsdl",
            operations=["UwvWbPersoonsInfo"],
        ),
    ]
}
