from unittest.mock import patch

from django.test import SimpleTestCase

import requests_mock
from glom import glom

from zgw_consumers_ext.tests.factories import ServiceFactory

from ..clients import get_brp_client
from ..constants import BRPVersions
from ..models import HaalCentraalConfig
from .utils import load_json_mock


class HaalCentraalFindPersonTests:
    """
    Mixin defining the actual tests to run for a particular client version.

    All client versions must support this set of functionality.

    You must implement the classmethod ``setUp`` to create the relevant service,
    for which you can then mock the API calls.
    """

    # specify in subclasses
    version: BRPVersions

    # possibly override for different versions, but at least v1 and v2 support both of these
    attributes_to_query = (
        "naam.voornamen",
        "naam.geslachtsnaam",
    )

    def setUp(self):
        super().setUp()  # type: ignore

        # set up patcher for the configuration
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
                oas="https://this.is.ignored",
            ),
            brp_personen_version=self.version,
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_find_person_succesfully(self):
        with get_brp_client() as client:
            raw_data = client.find_person(
                "999990676", attributes=self.attributes_to_query
            )

        values = {attr: glom(raw_data, attr) for attr in self.attributes_to_query}
        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)  # type: ignore

    def test_person_not_found(self):
        with get_brp_client() as client:
            raw_data = client.find_person(
                bsn="999990676", attributes=self.attributes_to_query
            )

        self.assertIsNone(raw_data)  # type: ignore

    def test_find_person_server_error(self):
        self.requests_mock.register_uri(
            requests_mock.ANY,
            requests_mock.ANY,
            status_code=500,
        )

        with get_brp_client() as client:
            raw_data = client.find_person(
                bsn="999990676", attributes=self.attributes_to_query
            )

        self.assertIsNone(raw_data)  # type: ignore

    def test_get_kinderen(self):
        with get_brp_client() as client:
            children = client.get_family_members(
                bsn="999990676", include_children=True, include_partner=False
            )

        self.assertEqual(len(children), 1)  # type: ignore
        child = children[0]
        self.assertEqual(child.bsn, "999991863")  # type: ignore
        self.assertEqual(child.name.voornamen, "Frieda")  # type: ignore
        self.assertEqual(child.name.voorvoegsel, "")  # type: ignore
        self.assertEqual(child.name.geslachtsnaam, "Kroket")  # type: ignore

    def test_get_partners(self):
        with get_brp_client() as client:
            partners = client.get_family_members(
                bsn="999990676", include_children=False, include_partner=True
            )

        self.assertEqual(len(partners), 1)  # type: ignore
        partner = partners[0]
        self.assertEqual(partner.bsn, "999991863")  # type: ignore
        self.assertEqual(partner.name.voornamen, "Frieda")  # type: ignore
        self.assertEqual(partner.name.voorvoegsel, "")  # type: ignore
        self.assertEqual(partner.name.geslachtsnaam, "Kroket")  # type: ignore

    def test_get_family_members(self):
        with get_brp_client() as client:
            family_members = client.get_family_members(
                bsn="999990676", include_children=True, include_partner=True
            )

        self.assertEqual(len(family_members), 2)  # type: ignore

        child = family_members[0]

        self.assertEqual(child.bsn, "999991111")  # type: ignore
        self.assertEqual(child.name.voornamen, "Fredo")  # type: ignore
        self.assertEqual(child.name.voorvoegsel, "")  # type: ignore
        self.assertEqual(child.name.geslachtsnaam, "Kroket")  # type: ignore

        partner = family_members[1]

        self.assertEqual(partner.bsn, "999992222")  # type: ignore
        self.assertEqual(partner.name.voornamen, "Frieda")  # type: ignore
        self.assertEqual(partner.name.voorvoegsel, "")  # type: ignore
        self.assertEqual(partner.name.geslachtsnaam, "Kroket")  # type: ignore

    def test_default_client_context(self):
        client = get_brp_client()

        self.assertIsNone(client.pre_request_context)  # type: ignore


class HaalCentraalFindPersonV1Test(HaalCentraalFindPersonTests, SimpleTestCase):
    version = BRPVersions.v13

    def test_find_person_succesfully(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1.json"),
        )
        super().test_find_person_succesfully()

    def test_person_not_found(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676", status_code=404
        )
        super().test_person_not_found()

    def test_get_kinderen(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v1/redoc#tag/Ingeschreven-Personen/operation/GetKinderen
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676/kinderen",
            json={
                "_links": {
                    "self": {
                        "href": "https://personen/api/ingeschrevenpersonen/999990676/kinderen",
                        "templated": False,
                        "title": "",
                    }
                },
                "_embedded": {
                    "kinderen": [
                        {
                            "burgerservicenummer": "999991863",
                            "leeftijd": 12,
                            "naam": {
                                "geslachtsnaam": "Kroket",
                                "voorletters": "F.",
                                "voornamen": "Frieda",
                                "voorvoegsel": "",
                                # "adellijkeTitelPredikaat": {...},
                                # "inOnderzoek": {...},
                            },
                            "geheimhoudingPersoonsgegevens": True,
                            # "inOnderzoek": {...},
                            # "geboorte": {...},
                            # "_links": {...},
                        }
                    ],
                },
            },
        )
        super().test_get_kinderen()

    def test_get_partners(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v1/redoc#tag/Ingeschreven-Personen/operation/GetPartners
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676/partners",
            json={
                "_links": {
                    "self": {
                        "href": "https://personen/api/ingeschrevenpersonen/999990676/partners",
                        "templated": False,
                        "title": "",
                    }
                },
                "_embedded": {
                    "partners": [
                        {
                            "burgerservicenummer": "999991863",
                            "naam": {
                                "geslachtsnaam": "Kroket",
                                "voorletters": "F.",
                                "voornamen": "Frieda",
                                "voorvoegsel": "",
                            },
                        }
                    ],
                },
            },
        )
        super().test_get_partners()

    def test_get_family_members(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v1/redoc#tag/Ingeschreven-Personen/operation/GetPartners
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676/partners",
            json={
                "_links": {
                    "self": {
                        "href": "https://personen/api/ingeschrevenpersonen/999990676/partners",
                        "templated": False,
                        "title": "",
                    }
                },
                "_embedded": {
                    "partners": [
                        {
                            "burgerservicenummer": "999992222",
                            "naam": {
                                "geslachtsnaam": "Kroket",
                                "voorletters": "F.",
                                "voornamen": "Frieda",
                                "voorvoegsel": "",
                            },
                        }
                    ],
                },
            },
        )
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v1/redoc#tag/Ingeschreven-Personen/operation/GetKinderen
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676/kinderen",
            json={
                "_links": {
                    "self": {
                        "href": "https://personen/api/ingeschrevenpersonen/999990676/kinderen",
                        "templated": False,
                        "title": "",
                    }
                },
                "_embedded": {
                    "kinderen": [
                        {
                            "burgerservicenummer": "999991111",
                            "leeftijd": 12,
                            "naam": {
                                "geslachtsnaam": "Kroket",
                                "voorletters": "F.",
                                "voornamen": "Fredo",
                                "voorvoegsel": "",
                            },
                            "geheimhoudingPersoonsgegevens": True,
                        }
                    ],
                },
            },
        )
        super().test_get_family_members()


class HaalCentraalFindPersonV2Test(HaalCentraalFindPersonTests, SimpleTestCase):
    version = BRPVersions.v20

    def test_find_person_succesfully(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_find_person_succesfully()

    def test_person_not_found(self):
        self.requests_mock.post("https://personen/api/personen", status_code=404)
        super().test_person_not_found()

    def test_find_person_without_personen_key(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock(
                "ingeschrevenpersonen.v2-full-find-personen-response.json"
            ),
        )
        super().test_person_not_found()

    def test_get_kinderen(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc#tag/Personen/operation/Personen
        self.requests_mock.post(
            "https://personen/api/personen",
            json={
                "type": "RaadpleegMetBurgerservicenummer",
                "personen": [
                    {
                        "kinderen": [
                            {
                                # only kinderen.burgerservicenummer and kinderen.naam are requested!
                                "burgerservicenummer": "999991863",
                                "naam": {
                                    "voornamen": "Frieda",
                                    "voorvoegsel": "",
                                    "geslachtsnaam": "Kroket",
                                    "voorletters": "F.",
                                    # "adellijkeTitelPredikaat": {...},
                                    # "inOnderzoek": {...},
                                },
                            }
                        ],
                    }
                ],
            },
        )
        super().test_get_kinderen()

    def test_get_kinderen_person_not_found_results(self):
        # TODO: replace this with VCR and the Docker container of BRP v2
        self.requests_mock.post(
            "https://personen/api/personen",
            json={
                "type": "RaadpleegMetBurgerservicenummer",
                "personen": [],
            },
        )

        with get_brp_client() as client:
            children = client.get_family_members(
                bsn="999990676", include_children=True, include_partner=False
            )

        self.assertEqual(children, [])

    def test_get_partners(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc#tag/Personen/operation/Personen
        self.requests_mock.post(
            "https://personen/api/personen",
            json={
                "type": "RaadpleegMetBurgerservicenummer",
                "personen": [
                    {
                        "partners": [
                            {
                                "burgerservicenummer": "999991863",
                                "naam": {
                                    "voornamen": "Frieda",  # Not all the names have voorvoegsels
                                    "geslachtsnaam": "Kroket",
                                    "voorletters": "F.",
                                },
                            }
                        ],
                    }
                ],
            },
        )
        super().test_get_partners()

    def test_get_family_members(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc#tag/Personen/operation/Personen
        self.requests_mock.post(
            "https://personen/api/personen",
            json={
                "type": "RaadpleegMetBurgerservicenummer",
                "personen": [
                    {
                        "partners": [
                            {
                                "burgerservicenummer": "999992222",
                                "naam": {
                                    "voornamen": "Frieda",  # Not all the names have voorvoegsels
                                    "geslachtsnaam": "Kroket",
                                    "voorletters": "F.",
                                },
                            }
                        ],
                        "kinderen": [
                            {
                                "burgerservicenummer": "999991111",
                                "naam": {
                                    "geslachtsnaam": "Kroket",
                                    "voorletters": "F.",
                                    "voornamen": "Fredo",
                                    "voorvoegsel": "",
                                },
                            }
                        ],
                    }
                ],
            },
        )
        super().test_get_family_members()


class ClientFactoryTests(SimpleTestCase):
    def test_invalid_version_raises_error(self):
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
                oas="https://this.is.ignored",
            ),
            brp_personen_version="0.999",
        )
        assert config.brp_personen_version not in BRPVersions.values

        with patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=config,
        ):
            with self.assertRaises(RuntimeError):
                get_brp_client()
