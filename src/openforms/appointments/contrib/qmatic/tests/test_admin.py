from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.tests.cache import clear_caches

from ..constants import CustomerFields


class QmaticConfigAdminTests(WebTest):
    def setUp(self):
        super().setUp()

        self.addCleanup(clear_caches)

    def test_customer_fields_are_listed(self):
        superuser = SuperUserFactory.create()
        admin_url = reverse("admin:qmatic_qmaticconfig_change", args=(1,))
        change_page = self.app.get(admin_url, user=superuser)
        form = change_page.forms["qmaticconfig_form"]

        fields = form.fields["required_customer_fields"]
        self.assertGreater(len(fields), 1)
        checked_field_values = [field.value for field in fields if field.checked]
        for value in checked_field_values:
            with self.subTest(f"{value=}"):
                self.assertIn(value, CustomerFields)
