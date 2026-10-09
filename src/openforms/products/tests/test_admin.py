from decimal import Decimal
from uuid import uuid4

from django.urls import reverse

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

    def test_producttype(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = ""
        form["price"] = ""
        form["producttype"] = str(product_uuid)
        form_response = form.submit()

        self.assertRedirects(
            form_response,
            reverse("admin:products_product_changelist"),
            fetch_redirect_response=False,
        )

        product = Product.objects.get()
        self.assertEqual(product.uuid, product_uuid)
        self.assertEqual(product.producttype, product_uuid)
        self.assertEqual(product.name, "")  # TODO: retrieve this from Open Product
        self.assertIsNone(product.price, None)  # TODO: retrieve this from Open Product

    def test_producttype_without_uuid(self):
        """
        Assert that the `producttype` UUID is used for the product's `uuid`.
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
        form["producttype"] = str(product_uuid)
        form_response = form.submit()

        self.assertRedirects(
            form_response,
            reverse("admin:products_product_changelist"),
            fetch_redirect_response=False,
        )

        product = Product.objects.get()
        self.assertEqual(product.uuid, product_uuid)

    def test_without_producttype(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = "Test product"
        form["price"] = "10"
        form["producttype"] = ""
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
        self.assertIsNone(product.producttype)

    def test_producttype_with_price(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        product_uuid = uuid4()
        form = response.forms["product_form"]
        form["uuid"] = str(product_uuid)
        form["name"] = ""
        form["price"] = 10
        form["producttype"] = str(product_uuid)
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,
            "Price cannot be filled in for products with a producttype.",
            html=True,
        )

    def test_no_producttype_and_no_price(self):
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        form = response.forms["product_form"]
        form["uuid"] = str(uuid4())
        form["name"] = "Invalid product"
        form["price"] = ""
        form["producttype"] = ""
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,
            "Price is required for products without a producttype.",
            html=True,
        )

    def test_product_with_different_uuids(self):
        """
        Assert that the `uuid` field is the same as the `producttype` if specified.
        """
        response = self.app.get(
            reverse("admin:products_product_add"),
            user=self.user,
        )
        form = response.forms["product_form"]
        form["uuid"] = str(uuid4())
        form["name"] = "Invalid product"
        form["price"] = 10
        form["producttype"] = str(uuid4())
        form_response = form.submit()

        self.assertEqual(200, form_response.status_code)
        self.assertContains(
            form_response,
            "Product UUID cannot be different from producttype when a producttype is specified.",
            html=True,
        )

    def test_read_only_fields(self):
        """
        Assert that certain fields are readonly fields whenever a producttype is specified.
        """
        product_uuid = str(uuid4())
        product = ProductFactory.create(
            uuid=product_uuid, producttype=product_uuid, price=None
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
        ProductFactory.create(uuid=product_uuid, producttype=product_uuid, price=None)

        response = self.app.get(
            reverse("admin:products_product_changelist"),
            user=self.user,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "icon-yes")
