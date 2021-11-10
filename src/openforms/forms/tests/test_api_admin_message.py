from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.admin import SubmitActions

from .factories import FormFactory


class FormAdminMessageTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.form = FormFactory.create()
        cls.endpoint = reverse(
            "api:form-admin-message", kwargs={"uuid_or_slug": cls.form.uuid}
        )
        cls.admin_user = SuperUserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_redirect_url_form_create_or_edit_regular_save(self):
        for is_create in (False, True):
            with self.subTest(is_create=is_create):
                data = {
                    "isCreate": is_create,
                    "submitAction": SubmitActions.save,
                }

                response = self.client.post(self.endpoint, data)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(
                    response.json()["redirectUrl"],
                    f"http://testserver{reverse('admin:forms_form_changelist')}",
                )

    def test_redirect_url_form_create_or_edit_save_and_add_another(self):
        for is_create in (False, True):
            with self.subTest(is_create=is_create):
                data = {
                    "isCreate": is_create,
                    "submitAction": SubmitActions.add_another,
                }

                response = self.client.post(self.endpoint, data)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(
                    response.json()["redirectUrl"],
                    f"http://testserver{reverse('admin:forms_form_add')}",
                )

    def test_redirect_url_form_create_or_edit_save_and_edit_again(self):
        for is_create in (False, True):
            with self.subTest(is_create=is_create):
                data = {
                    "isCreate": is_create,
                    "submitAction": SubmitActions.edit_again,
                }

                response = self.client.post(self.endpoint, data)

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(
                    response.json()["redirectUrl"],
                    f"http://testserver{reverse('admin:forms_form_change', args=(self.form.pk,))}",
                )
