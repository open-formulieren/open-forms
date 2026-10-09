import json
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from openproduct_client.structs.base import PaginatedResponseBody
from openproduct_client.structs.product_type import ContentLabel

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.products.models.product import Product
from openforms.products.tests.factories import ProductFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..models import ProductConfiguration
from .factories import OpenProductServiceFactory


@disable_admin_mfa()
@override_settings(LANGUAGE_CODE="en")
class ProductConfigurationAdminTests(OFVCRMixin, WebTest):
    def setUp(self):
        super().setUp()

        # we use cache for retrieving the results from the API so we have to clear that
        # for each test to get a fresh cache key (see clean method in the admin)
        self.addCleanup(cache.clear)
        self.addCleanup(ProductConfiguration.clear_cache)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()
        cls.opt_service = OpenProductServiceFactory.create(for_test_docker_compose=True)

        cls.url = reverse("admin:products_productconfiguration_change")

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


@disable_admin_mfa()
class ProductValidationAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.user = UserFactory.create(is_superuser=True, is_staff=True)

    def test_create_open_product(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = ""
        form["price"] = ""
        form["producttype_uuid"] = str(product_uuid)
        form_response = form.submit()

        self.assertRedirects(
            form_response,  # pyright: ignore[reportArgumentType]
            reverse("admin:products_product_changelist"),
            fetch_redirect_response=False,
        )

        product = Product.objects.get()
        self.assertEqual(product.uuid, product_uuid)
        self.assertEqual(product.producttype_uuid, product_uuid)
        self.assertEqual(product.name, "")  # TODO: retrieve this from Open Product
        self.assertIsNone(product.price, None)  # TODO: retrieve this from Open Product

    def test_create_open_product_reuses_producttype_uuid(self):
        """
        Assert that the ``producttype`` UUID is used for the product's ``uuid``.
        """
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = ""
        form["name"] = ""
        form["price"] = ""
        form["producttype_uuid"] = str(product_uuid)
        form_response = form.submit()

        self.assertRedirects(
            form_response,  # pyright: ignore[reportArgumentType]
            reverse("admin:products_product_changelist"),
            fetch_redirect_response=False,
        )

        product = Product.objects.get()
        self.assertEqual(product.uuid, product_uuid)

    def test_create_local_product(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = "Test product"
        form["price"] = "10"
        form["producttype_uuid"] = ""
        form_response = form.submit()

        self.assertRedirects(
            form_response,  # pyright: ignore[reportArgumentType]
            reverse("admin:products_product_changelist"),
            fetch_redirect_response=False,
        )

        product = Product.objects.get()
        self.assertEqual(product.uuid, product_uuid)
        self.assertEqual(product.name, "Test product")
        self.assertEqual(product.price, Decimal(10))
        self.assertIsNone(product.producttype_uuid)

    def test_create_local_product_name_required(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = ""
        form["price"] = "10"
        form["producttype_uuid"] = ""
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,  # pyright: ignore[reportArgumentType]
            _("Name is required for products without a producttype ID."),
            html=True,
        )

    def test_create_open_product_producttype_with_price(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = ""
        form["price"] = 10
        form["producttype_uuid"] = str(product_uuid)
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,  # pyright: ignore[reportArgumentType]
            _(
                "Price cannot be blank and can only be set for products without a producttype ID."
            ),
            html=True,
        )

    def test_create_open_product_producttype_with_name(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = "I should not be filled in"
        form["price"] = ""
        form["producttype_uuid"] = str(product_uuid)
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,  # pyright: ignore[reportArgumentType]
            _("Name cannot be filled in for products with a producttype ID."),
            html=True,
        )

    def test_create_no_producttype_and_no_price(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        form = response.forms["product_form"]
        form["uuid"] = str(uuid4())
        form["name"] = "Invalid product"
        form["price"] = ""
        form["producttype_uuid"] = ""
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,  # pyright: ignore[reportArgumentType]
            _("Price is required for products without a producttype ID."),
            html=True,
        )

    def test_read_only_fields(self):
        """
        Assert that certain fields are readonly fields whenever a producttype is specified.
        """
        product_uuid = str(uuid4())
        product = ProductFactory.create(
            uuid=product_uuid, producttype_uuid=product_uuid, price=None
        )

        response = self.app.get(
            reverse("admin:products_product_change", args=(str(product.pk),)),
            user=self.user,
        )
        self.assertEqual(response.status_code, 200)

        form = response.forms["product_form"]
        for field in ("name", "uuid", "producttype", "price"):
            with self.subTest(field=field):
                self.assertTrue(field not in form.fields)

    def test_changelist_with_producttype(self):
        """
        Assert that the green check mark icon is shown for Open Product products.
        """
        product_uuid = str(uuid4())
        ProductFactory.create(
            uuid=product_uuid, producttype_uuid=product_uuid, price=None
        )

        response = self.app.get(
            reverse("admin:products_product_changelist"),
            user=self.user,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "icon-yes")  # pyright: ignore[reportArgumentType]

    def test_producttype_uuid_filter(self):
        open_product_product = ProductFactory.create(
            producttype_uuid=uuid4(), price=None, name="External product"
        )
        local_product = ProductFactory.create(
            producttype_uuid=None, name="Local product", price=Decimal(20)
        )

        with self.subTest(name="Request without query params"):
            response = self.app.get(
                reverse("admin:products_product_changelist", query={}),
                user=self.user,
            )

            self.assertContains(response, local_product.name, html=True)  # pyright: ignore[reportArgumentType]
            self.assertContains(response, open_product_product.name, html=True)  # pyright: ignore[reportArgumentType]

        with self.subTest(name="Using local product filter"):
            response = self.app.get(
                reverse(
                    "admin:products_product_changelist", query={"open_product": "false"}
                ),
                user=self.user,
            )

            self.assertContains(response, local_product.name, html=True)  # pyright: ignore[reportArgumentType]
            self.assertNotContains(response, open_product_product.name, html=True)  # pyright: ignore[reportArgumentType]

        with self.subTest(name="Using Open Product product filter"):
            response = self.app.get(
                reverse(
                    "admin:products_product_changelist", query={"open_product": "true"}
                ),
                user=self.user,
            )

            self.assertNotContains(response, local_product.name, html=True)  # pyright: ignore[reportArgumentType]
            self.assertContains(response, open_product_product.name, html=True)  # pyright: ignore[reportArgumentType]
