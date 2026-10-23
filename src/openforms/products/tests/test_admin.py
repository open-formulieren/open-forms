import json
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from openproduct_client.structs.base import PaginatedResponseBody
from openproduct_client.structs.product_type import ContentLabel

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.tests.cache import clear_caches
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ProductConfiguration
from .factories import OpenProductServiceFactory


@disable_admin_mfa()
@override_settings(LANGUAGE_CODE="en")
class ProductConfigurationAdminTests(OFVCRMixin, WebTest):
    def setUp(self):
        super().setUp()

        self.addCleanup(lambda: ProductConfiguration.get_solo().delete())
        self.addCleanup(clear_caches)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()
        cls.opt_service = OpenProductServiceFactory.create()
        cls.url = reverse(
            "admin:products_productconfiguration_change", kwargs={"object_id": 1}
        )

    def test_no_data_provided(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms["productconfiguration_form"]
        form["open_product_service"] = ""
        form["content_labels"] = json.dumps([])

        form_submit_response = form.submit()

        self.assertEqual(form_submit_response.status_code, 200)
        self.assertContains(
            form_submit_response,  # pyright: ignore[reportArgumentType]
            _("This field is required."),
            html=True,
        )

    def test_existing_labels_provided(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms["productconfiguration_form"]
        form["open_product_service"] = str(self.opt_service.pk)
        form["content_labels"] = json.dumps(["Voorwaarden"])

        form_submit_response = form.submit().follow()

        self.assertEqual(form_submit_response.status_code, 200)
        self.assertContains(
            form_submit_response,  # pyright: ignore[reportArgumentType]
            _("ProductConfiguration object (1) was changed successfully."),
            html=True,
        )

    def test_wrong_labels_provided(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms["productconfiguration_form"]
        form["open_product_service"] = str(self.opt_service.pk)
        form["content_labels"] = json.dumps(["Voorwaarden", "another"])

        form_submit_response = form.submit()

        self.assertEqual(form_submit_response.status_code, 200)
        self.assertContains(
            form_submit_response,  # pyright: ignore[reportArgumentType]
            _("Unknown labels were provided: another."),
            html=True,
        )

    @patch(
        "openproduct_client.resources.product_type.content_label.ContentLabelResource.list"
    )
    def test_cache_is_used_instead_of_a_new_request(self, mocked_list_labels):
        mocked_list_labels.return_value = PaginatedResponseBody(
            count=2,
            next=None,
            previous=None,
            results=[ContentLabel(naam="Test1"), ContentLabel(naam="Test2")],
        )

        response = self.app.get(self.url, user=self.user)

        form = response.forms["productconfiguration_form"]
        form["open_product_service"] = str(self.opt_service.pk)
        form["content_labels"] = json.dumps(["Voorwaarden"])

        form.submit()

        form["content_labels"] = json.dumps(["another"])
        form.submit()

        mocked_list_labels.assert_called_once()
