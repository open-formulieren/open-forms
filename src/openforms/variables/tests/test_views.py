from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.forms.constants import FormVariableDataTypes


class GetStaticVariablesViewTest(APITestCase):
    def test_auth_required(self):
        url = reverse(
            "api:variables:static",
        )

        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["view_formvariable"]
        )
        url = reverse(
            "api:variables:static",
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @freeze_time("2021-07-16T21:15:00+00:00")
    def test_get_static_variables(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        url = reverse(
            "api:variables:static",
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertEqual(1, len(data))
        self.assertEqual(
            {
                "form": None,
                "form_definition": None,
                "name": "Now",
                "key": "now",
                "source": "",
                "prefill_plugin": "",
                "prefill_attribute": "",
                "data_type": FormVariableDataTypes.datetime,
                "data_format": "",
                "is_sensitive_data": False,
                "initial_value": "2021-07-16T21:15:00+00:00",
            },
            data[0],
        )
