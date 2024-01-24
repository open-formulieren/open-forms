import datetime
import json
import unittest
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

import lxml.etree
from bs4 import BeautifulSoup
from freezegun import freeze_time
from furl import furl
from privates.test import temp_private_root
from zeep.exceptions import Fault

from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ..client import NoServiceConfigured, get_client
from .factories import FAKE_BASE_URL, SUWINET_BASE_URL, SuwinetConfigFactory

DATA_DIR = Path(__file__).parent / "data"


class SuwinetConfigTests(TestCase):
    def test_client_requires_a_service(self):
        config = SuwinetConfigFactory.build(service=None)

        with self.assertRaises(NoServiceConfigured):
            get_client(config)

    def test_config_uses_local_wsdl(self):
        # DH gateway doesn't serve a wsdl... use our local wsdls
        SuwinetConfigFactory.create(
            service__url="",
            kadasterdossiergsd_binding_address=f"{SUWINET_BASE_URL}/KadasterDossierGSD-v0300/v1",
        )

        with get_client() as client:
            self.assertTrue(client.KadasterDossierGSD)

    @override_settings(LANGUAGE_CODE="en")
    def test_setting_a_wsdl_url_will_fail(self):
        config = SuwinetConfigFactory.build(
            service__url="http://www.soapclient.com/xml/soapresponder.wsdl"
        )
        with self.assertRaisesMessage(
            ValidationError,
            "Using a wsdl to describe all of Suwinet is not implemented.",
        ):
            config.clean()

    @override_settings(LANGUAGE_CODE="en")
    def test_setting_no_bindings_will_fail(self):
        config = SuwinetConfigFactory.build(
            service__url="",
        )
        with self.assertRaisesMessage(
            ValidationError,
            "Without any binding addresses, no Suwinet service can be used.",
        ):
            config.clean()

    def test_iterating_client_yields_configured_service_names(self):
        config = SuwinetConfigFactory.build(
            kadasterdossiergsd_binding_address=f"{SUWINET_BASE_URL}/KadasterDossierGSD-v0300/v1",
        )

        config.clean()
        client = get_client(config)

        self.assertEqual(len(client), 1)
        self.assertEqual(list(client), ["KadasterDossierGSD"])


@temp_private_root()
class SuwinetTestCase(OFVCRMixin, TestCase):
    VCR_TEST_FILES = DATA_DIR

    def _get_vcr(self, **kwargs):
        # filter the gateway address from cassettes
        def rewrite_body(body: bytes) -> bytes:
            return body.replace(
                SUWINET_BASE_URL.encode("utf8"), FAKE_BASE_URL.encode("utf8")
            ).replace(
                # ?oin paths at the root
                furl(SUWINET_BASE_URL).netloc.encode("utf8"),
                furl(FAKE_BASE_URL).netloc.encode("utf8"),
            )

        def rewrite_request(request):
            request.uri = request.uri.replace(SUWINET_BASE_URL, FAKE_BASE_URL)
            request.body = rewrite_body(request.body)
            return request

        def rewrite_response(response):
            response["body"]["string"] = rewrite_body(
                response["body"]["string"]
            )  # Convenient when developing against the gateway...
            # Layer 7 gateway faults are failures; they don't come from suwinet
            # if (
            #     b"http://www.layer7tech.com/ws/policy/fault"
            #     in response["body"]["string"]
            # ):
            #     # Fail the test and prevent saving the episode
            #     self.fail("Layer 7 Fault")

            return response

        # kwargs.setdefault("match_on", []).append("soap")
        kwargs["match_on"] = ["soap"]
        kwargs.setdefault("before_record_request", []).append(rewrite_request)
        kwargs.setdefault("before_record_response", []).append(rewrite_response)
        kwargs["decode_compressed_response"] = True

        vcr = super()._get_vcr(**kwargs)

        def soap_matcher(r1, r2):
            assert r1.uri == r2.uri
            assert r1.method == r2.method
            # disregard signatures in the envelope header
            b1 = BeautifulSoup(r1.body, features="lxml")
            b2 = BeautifulSoup(r2.body, features="lxml")
            assert list(b1.find("soap-env:body").children) == list(
                b2.find("soap-env:body").children
            )

        vcr.register_matcher("soap", soap_matcher)

        return vcr

    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

        # WSS signatures expire: freeze the time in CI
        if self.cassette.responses:
            now = self.cassette.responses[0]["headers"]["Date"][0]
            time_ctx = freeze_time(now)
            self.addCleanup(time_ctx.stop)
            time_ctx.start()


class SuwinetKadasterTests(SuwinetTestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        # This makes libxmlsec dump some error data to stderr
        # import xmlsec

        # xmlsec.enable_debug_trace(True)

        super().setUpTestData()
        SuwinetConfigFactory.create(
            kadasterdossiergsd_binding_address=f"{SUWINET_BASE_URL}/KadasterDossierGSD-v0300/v1",
        )
        cls.suwi_client = get_client()

    def test_client_as_a_mapping(self):
        with self.assertRaisesMessage(KeyError, "foo"):
            self.suwi_client["foo"]

        with self.assertRaisesMessage(
            KeyError, r"RDWDossierDigitaleDiensten not configured"
        ):
            self.suwi_client["RDWDossierDigitaleDiensten"]

        self.assertIn("KadasterDossierGSD", self.suwi_client)

    def test_client_dir(self):
        # tab completion
        attributes = dir(self.suwi_client)

        self.assertNotIn("RDWDossierDigitaleDiensten", attributes)
        self.assertIn("KadasterDossierGSD", attributes)
        self.assertIn("__dir__", attributes)

    def test_persoons_info_bsn_444444440(self):
        info = self.suwi_client.KadasterDossierGSD.PersoonsInfo("444444440")

        today = datetime.date.today()

        expected = {
            "ClientSuwi": {
                "Burgerservicenr": "444444440",
                "Voornamen": "Martin",
                "Voorvoegsel": "de",
                "SignificantDeelVanDeAchternaam": "Visser",
                "Geslacht": "1",
                "Geboortedat": "19440611",
                "DomicilieAdres": {
                    "StraatadresBag": {
                        "Locatieoms": None,
                        "Postcd": "1411EA",
                        "Woonplaatsnaam": "Naarden",
                        "Gemeentenaam": None,
                        "Gemeentedeel": None,
                        "Straatnaam": "Marktstraat",
                        "Huisnr": 12,
                        "Huisletter": None,
                        "Huisnrtoevoeging": None,
                        "AanduidingBijHuisnr": None,
                    },
                    "GeneriekAdresBuitenland": None,
                },
                "Correspondentieadres": {
                    "StraatadresBag": {
                        "Locatieoms": None,
                        "Postcd": "1411EA",
                        "Woonplaatsnaam": "Naarden",
                        "Gemeentenaam": None,
                        "Gemeentedeel": None,
                        "Straatnaam": "Marktstraat",
                        "Huisnr": 12,
                        "Huisletter": None,
                        "Huisnrtoevoeging": None,
                        "AanduidingBijHuisnr": None,
                    },
                    "Postbusadres": None,
                    "GeneriekAdresBuitenland": None,
                },
                "DatToestandKadaster": today.strftime("%Y%m%d"),
                "DatFiatteringKadaster": None,
                "Eigendom": {
                    "OnroerendeZaak": [
                        {
                            "DatToestandKadaster": None,
                            "DatFiatteringKadaster": None,
                            "CdTypeOnroerendeZaak": "A",
                            "DatOntstaan": "19650113",
                            "KadastraleAanduiding": {
                                "CdKadastraleGemeente": "633",
                                "KadastraleGemeentenaam": "Naarden",
                                "KadastraleSectie": "A",
                                "KadastraalPerceelnr": 2535,
                                "VolgnrKadastraalAppartementsrecht": 2,
                            },
                            "OmsKadastraalObject": "Bebouwd: Wonen (appartement)",
                            "ZakelijkRecht": [
                                {
                                    "OmsZakelijkRecht": "Eigendom (recht van)",
                                    "DatEZakelijkRecht": None,
                                }
                            ],
                            "LocatieOZ": [
                                {
                                    "StraatadresBag": {
                                        "Locatieoms": None,
                                        "Postcd": "1411EA",
                                        "Woonplaatsnaam": "Naarden",
                                        "Gemeentenaam": None,
                                        "Gemeentedeel": None,
                                        "Straatnaam": "Marktstraat",
                                        "Huisnr": 12,
                                        "Huisletter": None,
                                        "Huisnrtoevoeging": None,
                                        "AanduidingBijHuisnr": None,
                                    }
                                }
                            ],
                            "PubliekrechtelijkeBeperking": [],
                            "BedrKoopsom": {
                                "CdMunteenheid": "EUR",
                                "CdPositiefNegatief": None,
                                "WaardeBedr": 7525000,
                                "CdPeriodeEenheidGeldigheidBedr": None,
                            },
                            "JaarAankoop": 1965,
                            "WijzeVerkrijgingEigendom": None,
                            "IndMeerGerechtigden": "2",
                        }
                    ],
                    "IndEigendomOZVerleden": None,
                },
            },
            "FWI": None,
            "FWI__1": None,
            "NietsGevonden": None,
        }

        self.assertDictEqual(_to_dict(info), expected)

    def test_persoons_info_bsn_111111110(self):
        info = self.suwi_client.KadasterDossierGSD.PersoonsInfo("111111110")

        expected = {
            "ClientSuwi": {
                "Burgerservicenr": "111111110",
                "Voornamen": "Henk",
                "Voorvoegsel": None,
                "SignificantDeelVanDeAchternaam": "Jansen",
                "Geslacht": "1",
                "Geboortedat": "19600720",
                "DomicilieAdres": {
                    "StraatadresBag": {
                        "Locatieoms": None,
                        "Postcd": "8012TB",
                        "Woonplaatsnaam": "ZWOLLE",
                        "Gemeentenaam": None,
                        "Gemeentedeel": None,
                        "Straatnaam": "Van der Laenstraat",
                        "Huisnr": 121,
                        "Huisletter": None,
                        "Huisnrtoevoeging": None,
                        "AanduidingBijHuisnr": None,
                    },
                    "GeneriekAdresBuitenland": None,
                },
                "Correspondentieadres": None,
                "DatToestandKadaster": "20170317",
                "DatFiatteringKadaster": None,
                "Eigendom": {
                    "OnroerendeZaak": [
                        {
                            "DatToestandKadaster": None,
                            "DatFiatteringKadaster": None,
                            "CdTypeOnroerendeZaak": "P",
                            "DatOntstaan": "19890615",
                            "KadastraleAanduiding": {
                                "CdKadastraleGemeente": "1189",
                                "KadastraleGemeentenaam": "Zwolle",
                                "KadastraleSectie": "DD",
                                "KadastraalPerceelnr": 11482,
                                "VolgnrKadastraalAppartementsrecht": None,
                            },
                            "OmsKadastraalObject": "Bebouwd: Wonen",
                            "ZakelijkRecht": [
                                {
                                    "OmsZakelijkRecht": "Eigendom (recht van)",
                                    "DatEZakelijkRecht": None,
                                }
                            ],
                            "LocatieOZ": [],
                            "PubliekrechtelijkeBeperking": [
                                {
                                    "AantekeningKadastraalObject": {
                                        "DatEAantekeningKadastraalObject": None,
                                        "OmsAantekeningKadastraalObject": "Er zijn geen beperkingen bekend in de Landelijke Voorziening WKPB.",
                                    },
                                    "BetrokkenPersoonBestuursorgaan": None,
                                }
                            ],
                            "BedrKoopsom": None,
                            "JaarAankoop": None,
                            "WijzeVerkrijgingEigendom": None,
                            "IndMeerGerechtigden": "1",
                        },
                        {
                            "DatToestandKadaster": None,
                            "DatFiatteringKadaster": None,
                            "CdTypeOnroerendeZaak": "P",
                            "DatOntstaan": "19890615",
                            "KadastraleAanduiding": {
                                "CdKadastraleGemeente": "1189",
                                "KadastraleGemeentenaam": "Zwolle",
                                "KadastraleSectie": "G1",
                                "KadastraalPerceelnr": 43970,
                                "VolgnrKadastraalAppartementsrecht": None,
                            },
                            "OmsKadastraalObject": "Bebouwd: Wonen",
                            "ZakelijkRecht": [
                                {
                                    "OmsZakelijkRecht": "Eigendom (recht van)",
                                    "DatEZakelijkRecht": None,
                                }
                            ],
                            "LocatieOZ": [],
                            "PubliekrechtelijkeBeperking": [
                                {
                                    "AantekeningKadastraalObject": {
                                        "DatEAantekeningKadastraalObject": None,
                                        "OmsAantekeningKadastraalObject": "Er zijn geen beperkingen bekend in de Landelijke Voorziening WKPB.",
                                    },
                                    "BetrokkenPersoonBestuursorgaan": None,
                                }
                            ],
                            "BedrKoopsom": None,
                            "JaarAankoop": None,
                            "WijzeVerkrijgingEigendom": None,
                            "IndMeerGerechtigden": "1",
                        },
                        {
                            "DatToestandKadaster": None,
                            "DatFiatteringKadaster": None,
                            "CdTypeOnroerendeZaak": "P",
                            "DatOntstaan": "19890615",
                            "KadastraleAanduiding": {
                                "CdKadastraleGemeente": "277",
                                "KadastraleGemeentenaam": "Hilversum",
                                "KadastraleSectie": "HH",
                                "KadastraalPerceelnr": 12051,
                                "VolgnrKadastraalAppartementsrecht": None,
                            },
                            "OmsKadastraalObject": "Bebouwd: Wonen",
                            "ZakelijkRecht": [
                                {
                                    "OmsZakelijkRecht": "Eigendom (recht van)",
                                    "DatEZakelijkRecht": None,
                                }
                            ],
                            "LocatieOZ": [],
                            "PubliekrechtelijkeBeperking": [
                                {
                                    "AantekeningKadastraalObject": {
                                        "DatEAantekeningKadastraalObject": None,
                                        "OmsAantekeningKadastraalObject": "Er zijn geen beperkingen bekend in de Landelijke Voorziening WKPB.",
                                    },
                                    "BetrokkenPersoonBestuursorgaan": None,
                                }
                            ],
                            "BedrKoopsom": None,
                            "JaarAankoop": None,
                            "WijzeVerkrijgingEigendom": None,
                            "IndMeerGerechtigden": "1",
                        },
                        {
                            "DatToestandKadaster": None,
                            "DatFiatteringKadaster": None,
                            "CdTypeOnroerendeZaak": "P",
                            "DatOntstaan": "19890615",
                            "KadastraleAanduiding": {
                                "CdKadastraleGemeente": "1189",
                                "KadastraleGemeentenaam": "Zwolle",
                                "KadastraleSectie": "G1",
                                "KadastraalPerceelnr": 43980,
                                "VolgnrKadastraalAppartementsrecht": None,
                            },
                            "OmsKadastraalObject": "Bebouwd: Wonen",
                            "ZakelijkRecht": [
                                {
                                    "OmsZakelijkRecht": "Eigendom (recht van)",
                                    "DatEZakelijkRecht": None,
                                }
                            ],
                            "LocatieOZ": [
                                {
                                    "StraatadresBag": {
                                        "Locatieoms": None,
                                        "Postcd": "8012TB",
                                        "Woonplaatsnaam": "Zwolle",
                                        "Gemeentenaam": None,
                                        "Gemeentedeel": None,
                                        "Straatnaam": "Van der Laenstraat",
                                        "Huisnr": 121,
                                        "Huisletter": None,
                                        "Huisnrtoevoeging": None,
                                        "AanduidingBijHuisnr": None,
                                    }
                                }
                            ],
                            "PubliekrechtelijkeBeperking": [
                                {
                                    "AantekeningKadastraalObject": {
                                        "DatEAantekeningKadastraalObject": None,
                                        "OmsAantekeningKadastraalObject": "Er zijn geen beperkingen bekend in de Landelijke Voorziening WKPB.",
                                    },
                                    "BetrokkenPersoonBestuursorgaan": None,
                                }
                            ],
                            "BedrKoopsom": None,
                            "JaarAankoop": None,
                            "WijzeVerkrijgingEigendom": None,
                            "IndMeerGerechtigden": "1",
                        },
                    ],
                    "IndEigendomOZVerleden": None,
                },
            },
            "FWI": None,
            "FWI__1": None,
            "NietsGevonden": None,
        }

        self.assertDictEqual(_to_dict(info), expected)


class SuwinetRDWDossierDigitaleDienstenTests(SuwinetTestCase):
    VCR_TEST_FILES = DATA_DIR

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        SuwinetConfigFactory.create(
            rdwdossierdigitalediensten_binding_address=f"{SUWINET_BASE_URL}/RDWDossierDigitaleDiensten-v0200/v1",
        )
        cls.suwi_client = get_client()

    @unittest.expectedFailure
    def test_test_bsns(self):
        # TODO This fails to get through the gateway
        bsns = [
            "111111110",
            "112233454",
            "444444440",
            "999996769",
        ]
        client = self.suwi_client
        for bsn in bsns:
            with self.subTest(bsn=bsn):
                try:
                    resp = client.RDWDossierDigitaleDiensten.VoertuigbezitInfoPersoon(
                        bsn
                    )
                    self.assertTrue(resp)
                except Fault as unpickalable_exception:
                    # make 🥒
                    unpickalable_exception.detail = lxml.etree.tounicode(
                        unpickalable_exception.detail
                    )
                    raise unpickalable_exception


def _to_dict(zeep_response):
    "Return a dict for a zeep.Client response"

    def default(o):
        try:
            return o.__json__()
        except AttributeError:
            raise TypeError

    return json.loads(json.dumps(zeep_response, default=default))
