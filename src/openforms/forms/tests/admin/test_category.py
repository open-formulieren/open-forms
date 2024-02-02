from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import CategoryFactory, FormFactory


@disable_admin_mfa()
class TestCategoryAdmin(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()

    def test_categories_list(self):
        url = reverse("admin:forms_category_changelist")
        root1, root2 = CategoryFactory.create_batch(2)
        child1 = CategoryFactory.create(parent=root1)
        FormFactory.create_batch(3, category=root2)
        FormFactory.create(category=child1)
        FormFactory.create(category=None)

        changelist = self.app.get(url, user=self.user)

        self.assertEqual(changelist.status_code, 200)

        with self.subTest("Categories shown"):
            self.assertContains(changelist, root1.name)
            self.assertContains(changelist, root2.name)
            self.assertContains(changelist, child1.name)

        with self.subTest("Form counts listed"):
            # 3rd row is the second root
            root2_row = changelist.pyquery("tbody tr").eq(2)
            td_count = root2_row.find("td.field-form_count")
            self.assertEqual(td_count.text(), "3")

            # 2nd row is the child of root 1
            child1_row = changelist.pyquery("tbody tr").eq(1)
            td_count = child1_row.find("td.field-form_count")
            self.assertEqual(td_count.text(), "1")

            # 1st row is the second root
            root1_row = changelist.pyquery("tbody tr").eq(0)
            td_count = root1_row.find("td.field-form_count")
            self.assertEqual(td_count.text(), "0")
