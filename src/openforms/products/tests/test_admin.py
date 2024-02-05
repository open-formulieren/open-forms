from decimal import Decimal

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory

from ..models import Product


class ProductAdminTests(WebTest):
    def test_product_with_valid_price_is_saved(self):
        superuser = SuperUserFactory.create()
        admin_url = reverse("admin:products_product_add")
        create_page = self.app.get(admin_url, user=superuser)
        form = create_page.form
        form["name"] = "example product"
        form["price"] = Decimal("10.00")
        response = form.submit()

        product = Product.objects.get()

        self.assertRedirects(response, reverse("admin:products_product_changelist"))
        self.assertEqual(product.name, "example product")

    def test_product_with_invalid_price_is_saved(self):
        superuser = SuperUserFactory.create()
        admin_url = reverse("admin:products_product_add")
        create_page = self.app.get(admin_url, user=superuser)
        form = create_page.form
        form["name"] = "example product"
        form["price"] = Decimal("0.00")
        response = form.submit()

        expected_error = [[_("The value must be greater than 0.")]]

        self.assertEqual(response.context["errors"], expected_error)
        self.assertFalse(Product.objects.exists())
