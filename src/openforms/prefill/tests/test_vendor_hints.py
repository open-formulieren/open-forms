from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from openforms.config.constants import FamilyMembersDataAPIChoices

from ..contrib.customer_interactions.plugin import CommunicationPreferences
from ..contrib.family_members.plugin import FamilyMembersPrefill
from ..contrib.haalcentraal_brp.plugin import HaalCentraalPrefill
from ..contrib.kvk.plugin import KVK_KVKNumberPrefill
from ..contrib.objects_api.plugin import ObjectsAPIPrefill
from ..contrib.stufbg.plugin import StufBgPrefill
from ..contrib.suwinet.plugin import SuwinetPrefill


class VendorHintTests(SimpleTestCase):
    def test_objects_api_uses_objects_service_api_root(self):
        group = SimpleNamespace(
            objects_service=SimpleNamespace(api_root="https://objects.example/api/")
        )

        self.assertEqual(
            ObjectsAPIPrefill("objects-api").get_vendor_hint(
                {"objects_api_group": group}
            ),
            "https://objects.example/api/",
        )

    def test_customer_interactions_uses_service_api_root(self):
        group = SimpleNamespace(
            customer_interactions_service=SimpleNamespace(
                api_root="https://klant.example/api/"
            )
        )

        self.assertEqual(
            CommunicationPreferences("customer").get_vendor_hint(
                {"customer_interactions_api_group": group}
            ),
            "https://klant.example/api/",
        )

    @patch("openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo")
    def test_haal_centraal_uses_service_api_root(self, get_solo):
        get_solo.return_value = SimpleNamespace(
            brp_personen_service=SimpleNamespace(
                api_root="https://personen.example/api/"
            )
        )

        self.assertEqual(
            HaalCentraalPrefill("haalcentraal").get_vendor_hint({}),
            "https://personen.example/api/",
        )

    @patch("openforms.contrib.kvk.models.KVKConfig.get_solo")
    def test_kvk_uses_configured_service_api_root(self, get_solo):
        get_solo.return_value = SimpleNamespace(
            profile_service=SimpleNamespace(api_root="https://kvk.example/api/"),
            branch_profile_service=None,
        )

        self.assertEqual(
            KVK_KVKNumberPrefill("kvk").get_vendor_hint({}),
            "https://kvk.example/api/",
        )

    @patch("stuf.stuf_bg.models.StufBGConfig.get_solo")
    def test_stuf_bg_uses_soap_endpoint(self, get_solo):
        get_solo.return_value = SimpleNamespace(
            service=SimpleNamespace(
                soap_service=SimpleNamespace(url="https://soap.example/bg")
            )
        )

        self.assertEqual(
            StufBgPrefill("stufbg").get_vendor_hint({}),
            "https://soap.example/bg",
        )

    @patch("suwinet.models.SuwinetConfig.get_solo")
    def test_suwinet_uses_service_url(self, get_solo):
        get_solo.return_value = SimpleNamespace(
            service=SimpleNamespace(url="https://soap.example/suwinet")
        )

        self.assertEqual(
            SuwinetPrefill("suwinet").get_vendor_hint({}),
            "https://soap.example/suwinet",
        )

    @patch("openforms.config.models.GlobalConfiguration.get_solo")
    @patch("openforms.contrib.haal_centraal.models.HaalCentraalConfig.get_solo")
    def test_family_members_haal_centraal(self, get_hc_solo, get_global_solo):
        get_global_solo.return_value = SimpleNamespace(
            family_members_data_api=FamilyMembersDataAPIChoices.haal_centraal
        )
        get_hc_solo.return_value = SimpleNamespace(
            brp_personen_service=SimpleNamespace(api_root="https://brp.example/api/")
        )

        self.assertEqual(
            FamilyMembersPrefill("family_members").get_vendor_hint({}),
            "https://brp.example/api/",
        )

    @patch("openforms.config.models.GlobalConfiguration.get_solo")
    @patch("stuf.stuf_bg.models.StufBGConfig.get_solo")
    def test_family_members_stuf_bg(self, get_stuf_solo, get_global_solo):
        get_global_solo.return_value = SimpleNamespace(
            family_members_data_api=FamilyMembersDataAPIChoices.stuf_bg
        )
        get_stuf_solo.return_value = SimpleNamespace(
            service=SimpleNamespace(
                soap_service=SimpleNamespace(url="https://soap.example/bg")
            )
        )

        self.assertEqual(
            FamilyMembersPrefill("family_members").get_vendor_hint({}),
            "https://soap.example/bg",
        )

    @patch("openforms.contrib.objects_api.models.ObjectsAPIGroupConfig.objects.filter")
    def test_objects_api_with_slug_from_db(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            objects_service=SimpleNamespace(api_root="https://objects.example/api/")
        )

        self.assertEqual(
            ObjectsAPIPrefill("objects-api").get_vendor_hint(
                {"objects_api_group": "my-group"}
            ),
            "https://objects.example/api/",
        )
        self.assertIsNone(ObjectsAPIPrefill("objects-api").get_vendor_hint({}))

    @patch(
        "openforms.contrib.customer_interactions.models.CustomerInteractionsAPIGroupConfig.objects.filter"
    )
    def test_customer_interactions_with_slug_from_db(self, mock_filter):
        mock_filter.return_value.first.return_value = SimpleNamespace(
            customer_interactions_service=SimpleNamespace(
                api_root="https://klant.example/api/"
            )
        )

        self.assertEqual(
            CommunicationPreferences("customer").get_vendor_hint(
                {"customer_interactions_api_group": "my-slug"}
            ),
            "https://klant.example/api/",
        )
        self.assertIsNone(CommunicationPreferences("customer").get_vendor_hint({}))
