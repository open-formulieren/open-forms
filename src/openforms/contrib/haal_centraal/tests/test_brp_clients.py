from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, tag

import requests_mock
from glom import glom
from zgw_consumers.test.factories import ServiceFactory

from openforms.authentication.service import AuthAttribute
from openforms.authentication.utils import store_registrator_details
from openforms.config.models import GlobalConfiguration
from openforms.pre_requests.base import PreRequestHookBase
from openforms.pre_requests.registry import Registry
from openforms.submissions.tests.factories import SubmissionFactory

from ..clients import get_brp_client
from ..constants import DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER, BRPVersions
from ..models import BRPPersonenRequestOptions, HaalCentraalConfig
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
            ),
            brp_personen_version=self.version,
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)  # type: ignore

        global_config = GlobalConfiguration()
        global_config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
            return_value=global_config,
        )
        global_config_patcher.start()
        self.addCleanup(global_config_patcher.stop)  # type: ignore

        # prepare a requests mock instance to wire up the mocks
        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)  # type: ignore

    def test_find_person_succesfully(self, bsn):
        with get_brp_client() as client:
            raw_data = client.find_persons([bsn], attributes=self.attributes_to_query)

        assert raw_data
        values = {attr: glom(raw_data[bsn], attr) for attr in self.attributes_to_query}
        expected = {
            "naam.voornamen": "Cornelia Francisca",
            "naam.geslachtsnaam": "Wiegman",
        }
        self.assertEqual(values, expected)  # type: ignore

    def test_person_not_found(self):
        with get_brp_client() as client:
            raw_data = client.find_persons(
                bsns=["999990676"], attributes=self.attributes_to_query
            )

        self.assertIsNone(raw_data)  # type: ignore

    def test_find_person_server_error(self):
        self.requests_mock.register_uri(
            requests_mock.ANY,
            requests_mock.ANY,
            status_code=500,
        )

        with get_brp_client() as client:
            raw_data = client.find_persons(
                bsns=["999990676"], attributes=self.attributes_to_query
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
        self.assertEqual(child.first_names, "Frieda")  # type: ignore
        self.assertEqual(child.affixes, "")  # type: ignore
        self.assertEqual(child.last_name, "Kroket")  # type: ignore

    def test_get_kinderen_no_bsn(self):
        with get_brp_client() as client:
            children = client.get_family_members(
                bsn="999990676", include_children=True, include_partner=False
            )

        self.assertEqual(len(children), 0)  # type: ignore

    def test_get_partners(self):
        with get_brp_client() as client:
            partners = client.get_family_members(
                bsn="999990676", include_children=False, include_partner=True
            )

        self.assertEqual(len(partners), 1)  # type: ignore
        partner = partners[0]
        self.assertEqual(partner.bsn, "999991863")  # type: ignore
        self.assertEqual(partner.first_names, "Frieda")  # type: ignore
        self.assertEqual(partner.affixes, "")  # type: ignore
        self.assertEqual(partner.last_name, "Kroket")  # type: ignore

    def test_partner_without_bsn(self):
        with get_brp_client() as client:
            partners = client.get_family_members(
                bsn="999990676", include_children=False, include_partner=True
            )

        self.assertEqual(len(partners), 0)  # type: ignore

    def test_get_family_members(self):
        with get_brp_client() as client:
            family_members = client.get_family_members(
                bsn="999990676", include_children=True, include_partner=True
            )

        self.assertEqual(len(family_members), 2)  # type: ignore

        child = family_members[0]

        self.assertEqual(child.bsn, "999991111")  # type: ignore
        self.assertEqual(child.first_names, "Fredo")  # type: ignore
        self.assertEqual(child.affixes, "")  # type: ignore
        self.assertEqual(child.last_name, "Kroket")  # type: ignore

        partner = family_members[1]

        self.assertEqual(partner.bsn, "999992222")  # type: ignore
        self.assertEqual(partner.first_names, "Frieda")  # type: ignore
        self.assertEqual(partner.affixes, "")  # type: ignore
        self.assertEqual(partner.last_name, "Kroket")  # type: ignore

    def test_default_client_context(self):
        client = get_brp_client()

        self.assertIsNone(client.pre_request_context)  # type: ignore

    @tag("gh-4713")
    def test_pre_request_hooks_called(self):
        """
        Regression test for #4713, assert that the pre request hooks are called with the
        expected context to make sure that token exchange works properly
        """
        pre_req_register = Registry()
        mock = MagicMock()

        @pre_req_register("test")
        class PreRequestHook(PreRequestHookBase):
            def __call__(self, *args, **kwargs):
                mock(*args, **kwargs)

        submission_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backend="demo",
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="71291440",
            auth_info__plugin="demo",
        )
        client = get_brp_client(submission_bsn)

        with patch("openforms.pre_requests.clients.registry", new=pre_req_register):
            client.find_persons(["999990676"], attributes=self.attributes_to_query)

        self.assertEqual(mock.call_count, 1)  # 1 API calls expected
        context = mock.call_args.kwargs["context"]
        self.assertEqual(context, {"submission": submission_bsn})  # type: ignore


class HaalCentraalFindPersonV1Test(HaalCentraalFindPersonTests, TestCase):
    version = BRPVersions.v13

    def test_find_person_succesfully(self, bsn=None):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1.json"),
        )
        super().test_find_person_succesfully("999990676")

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

    def test_get_kinderen_no_bsn(self):
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
                            "leeftijd": 12,
                            "naam": {
                                "geslachtsnaam": "Kroket",
                                "voorletters": "F.",
                                "voornamen": "Frieda",
                                "voorvoegsel": "",
                            },
                            "geheimhoudingPersoonsgegevens": True,
                        }
                    ],
                },
            },
        )
        super().test_get_kinderen_no_bsn()

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

    def test_partner_without_bsn(self):
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
        super().test_partner_without_bsn()

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

    def test_pre_request_hooks_called(self):
        self.requests_mock.get(
            "https://personen/api/ingeschrevenpersonen/999990676",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v1.json"),
        )
        super().test_pre_request_hooks_called()


class HaalCentraalFindPersonV2Test(HaalCentraalFindPersonTests, TestCase):
    version = BRPVersions.v20

    def test_find_person_succesfully(self, bsn=None):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_find_person_succesfully("999990676")

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

    def test_get_kinderen_no_bsn(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc#tag/Personen/operation/Personen
        self.requests_mock.post(
            "https://personen/api/personen",
            json={
                "type": "RaadpleegMetBurgerservicenummer",
                "personen": [
                    {
                        "kinderen": [
                            {
                                "naam": {
                                    "voornamen": "Frieda",
                                    "voorvoegsel": "",
                                    "geslachtsnaam": "Kroket",
                                    "voorletters": "F.",
                                },
                            }
                        ],
                    }
                ],
            },
        )
        super().test_get_kinderen_no_bsn()

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
                                    "voorvoegsel": "",
                                },
                            }
                        ],
                    }
                ],
            },
        )
        super().test_get_partners()

    def test_partner_without_bsn(self):
        # https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/redoc#tag/Personen/operation/Personen
        self.requests_mock.post(
            "https://personen/api/personen",
            json={
                "type": "RaadpleegMetBurgerservicenummer",
                "personen": [
                    {
                        "partners": [
                            {
                                "naam": {
                                    "voornamen": "Jean Marie",
                                    "geslachtsnaam": "Beaudelaire",
                                    "voorletters": "J.M.",
                                }
                            }
                        ],
                    }
                ],
            },
        )
        super().test_partner_without_bsn()

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
                                    "voorvoegsel": "",
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

    def test_pre_request_hooks_called(self):
        self.requests_mock.post(
            "https://personen/api/personen",
            status_code=200,
            json=load_json_mock("ingeschrevenpersonen.v2-full.json"),
        )
        super().test_pre_request_hooks_called()


class ClientFactoryInvalidVersionTests(SimpleTestCase):
    def test_invalid_version_raises_error(self):
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
            ),
            brp_personen_version="0.999",
        )
        assert config.brp_personen_version not in BRPVersions.values

        with (
            patch(
                "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
                return_value=config,
            ),
            patch(
                "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
                return_value=GlobalConfiguration(),
            ),
        ):
            with self.assertRaises(RuntimeError):
                get_brp_client(SubmissionFactory.build())


class HaalCentraalXHeadersTests(TestCase):
    def setUp(self):
        super().setUp()

        # set up patcher for the configuration
        config = HaalCentraalConfig(
            brp_personen_service=ServiceFactory.build(
                api_root="https://personen/api/",
            ),
            brp_personen_version=BRPVersions.v20,
            default_brp_personen_purpose_limitation_header_value="BRPACT-AanschrijvenZakelijkGerechtigde",
            default_brp_personen_processing_header_value="Financiële administratie@Correspondentie factuur",
        )
        config_patcher = patch(
            "openforms.contrib.haal_centraal.clients.HaalCentraalConfig.get_solo",
            return_value=config,
        )
        config_patcher.start()
        self.addCleanup(config_patcher.stop)

        self.requests_mock = requests_mock.Mocker()
        self.requests_mock.start()
        self.addCleanup(self.requests_mock.stop)

    @patch(
        "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(),
    )
    def test_uses_default_headers(self, m):
        self.requests_mock.register_uri(
            requests_mock.ANY, requests_mock.ANY, status_code=200
        )
        client = get_brp_client()
        client.post("irrelevant")

        request_headers = self.requests_mock.last_request.headers
        self.assertEqual(
            request_headers["x-doelbinding"], "BRPACT-AanschrijvenZakelijkGerechtigde"
        )
        self.assertEqual(
            request_headers["x-verwerking"],
            "Financiële administratie@Correspondentie factuur",
        )
        self.assertEqual(
            request_headers["x-gebruiker"], DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER
        )
        self.assertEqual(request_headers["x-origin-oin"], "")

    @patch(
        "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(),
    )
    def test_uses_haal_centraal_options(self, m):
        submission = SubmissionFactory.create()
        BRPPersonenRequestOptions.objects.create(
            form=submission.form,
            brp_personen_purpose_limitation_header_value="OVERRIDDEN_BRPACT-AanschrijvenZakelijkGerechtigde",
            brp_personen_processing_header_value="OVERRIDDEN_Financiële administratie@Correspondentie factuur",
        )

        self.requests_mock.register_uri(
            requests_mock.ANY, requests_mock.ANY, status_code=200
        )

        client = get_brp_client(submission)
        client.post("irrelevant")

        request_headers = self.requests_mock.last_request.headers

        self.assertEqual(
            request_headers["x-doelbinding"],
            "OVERRIDDEN_BRPACT-AanschrijvenZakelijkGerechtigde",
        )
        self.assertEqual(
            request_headers["x-verwerking"],
            "OVERRIDDEN_Financiële administratie@Correspondentie factuur",
        )

    @patch(
        "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(organization_oin="oin"),
    )
    def test_uses_organization_oin(self, m):
        self.requests_mock.register_uri(
            requests_mock.ANY, requests_mock.ANY, status_code=200
        )

        client = get_brp_client()
        client.post("irrelevant")

        request_headers = self.requests_mock.last_request.headers
        self.assertEqual(request_headers["x-origin-oin"], "oin")

    @patch(
        "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(),
    )
    def test_uses_registrator_attribute(self, m):
        submission = SubmissionFactory.create()
        store_registrator_details(
            submission,
            {
                "attribute": AuthAttribute.employee_id,
                "plugin": "irrelevant",
                "value": "test_employee_id",
            },
        )

        self.requests_mock.register_uri(
            requests_mock.ANY, requests_mock.ANY, status_code=200
        )

        client = get_brp_client(submission)
        client.post("irrelevant")

        request_headers = self.requests_mock.last_request.headers
        self.assertEqual(request_headers["x-gebruiker"], "test_employee_id")

    @patch(
        "openforms.contrib.haal_centraal.clients.GlobalConfiguration.get_solo",
        return_value=GlobalConfiguration(),
    )
    def test_skips_registrator_attribute(self, m):
        """Tests the registrator attribute is not used if not an employee id."""
        submission = SubmissionFactory.create()
        store_registrator_details(
            submission,
            {
                "attribute": AuthAttribute.pseudo,
                "plugin": "irrelevant",
                "value": "test_pseudo",
            },
        )

        self.requests_mock.register_uri(
            requests_mock.ANY, requests_mock.ANY, status_code=200
        )

        client = get_brp_client(submission)
        client.post("irrelevant")

        request_headers = self.requests_mock.last_request.headers
        self.assertNotEqual(request_headers["x-gebruiker"], "test_pseudo")
