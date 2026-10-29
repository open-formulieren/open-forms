from decimal import Decimal
from uuid import uuid4

from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import UserFactory
from openforms.products.models.product import Product
from openforms.products.tests.factories import ProductFactory


@disable_admin_mfa()
class ProductValidationTests(WebTest):
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
            form_response,
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
            form_response,
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
            form_response,
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
            form_response,
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
            form_response,
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
            form_response,
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
            form_response,
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
        self.assertContains(response, "icon-yes")

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

            self.assertContains(response, local_product.name, html=True)
            self.assertContains(response, open_product_product.name, html=True)

        with self.subTest(name="Using local product filter"):
            response = self.app.get(
                reverse(
                    "admin:products_product_changelist", query={"open_product": "false"}
                ),
                user=self.user,
            )

            self.assertContains(response, local_product.name, html=True)
            self.assertNotContains(response, open_product_product.name, html=True)

        with self.subTest(name="Using Open Product product filter"):
            response = self.app.get(
                reverse(
                    "admin:products_product_changelist", query={"open_product": "true"}
                ),
                user=self.user,
            )

            self.assertNotContains(response, local_product.name, html=True)
            self.assertContains(response, open_product_product.name, html=True)
