from decimal import Decimal

from rest_framework import status
from rest_framework.reverse import reverse, reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory, UserFactory
from openforms.submissions.tests.mixins import VariablesTestMixin

from ..models import FormPriceLogic
from .factories import FormFactory, FormPriceLogicFactory


class FormPriceLogicBulkAPITests(VariablesTestMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = SuperUserFactory.create()
        cls.form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )
        cls.form_url = reverse(
            "api:form-detail", kwargs={"uuid_or_slug": cls.form.uuid}
        )

    def test_auth_required(self):
        response = self.client.get(
            reverse_lazy(
                "api:form-price-logic-rules", kwargs={"uuid_or_slug": self.form.uuid}
            )
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_staff_user_required(self):
        user = UserFactory.create(is_staff=False)
        self.client.force_authenticate(user)

        response = self.client.get(
            reverse_lazy(
                "api:form-price-logic-rules", kwargs={"uuid_or_slug": self.form.uuid}
            )
        )

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_list_and_filter_price_logic(self):
        self.client.force_authenticate(self.superuser)
        fpl1, fpl2 = FormPriceLogicFactory.create_batch(2)
        assert fpl1.form != fpl2.form

        url = reverse(
            "api:form-price-logic-rules", kwargs={"uuid_or_slug": fpl1.form.uuid}
        )
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response_data = response.json()
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["uuid"], str(fpl1.uuid))

    def test_create_price_logic(self):
        self.client.force_authenticate(user=self.superuser)
        price_logic_data = [
            {
                "form": f"http://testserver{self.form_url}",
                "json_logic_trigger": {
                    "==": [
                        {"var": "step1_textfield1"},
                        "test",
                    ]
                },
                "price": "15.00",
            }
        ]

        url = reverse(
            "api:form-price-logic-rules", kwargs={"uuid_or_slug": self.form.uuid}
        )
        response = self.client.put(url, data=price_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        price_logics_qs = FormPriceLogic.objects.all()
        self.assertEqual(price_logics_qs.count(), 1)
        price_logic = price_logics_qs.get()
        self.assertEqual(price_logic.form, self.form)
        self.assertEqual(price_logic.price, Decimal("15.00"))

    def test_create_logic_with_dates(self):
        self.client.force_authenticate(user=self.superuser)
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "datetime",
                        "key": "dateOfBirth",
                    }
                ]
            },
        )
        form_url = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        price_logic_data = [
            {
                "form": f"http://testserver{form_url}",
                "json_logic_trigger": {
                    ">": [
                        {"date": {"var": "dateOfBirth"}},
                        {"-": [{"today": []}, {"rdelta": [18]}]},
                    ]
                },
                "price": "15.00",
            }
        ]

        url = reverse("api:form-price-logic-rules", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.put(url, data=price_logic_data)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_delete_price_logic(self):
        self.client.force_authenticate(user=self.superuser)
        price_rule = FormPriceLogicFactory.create(form__generate_minimal_setup=True)

        url = reverse(
            "api:form-price-logic-rules", kwargs={"uuid_or_slug": price_rule.form.uuid}
        )

        response = self.client.put(url, data=[])

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertFalse(FormPriceLogic.objects.exists())

    def test_invalid_logic_trigger(self):
        self.client.force_authenticate(user=self.superuser)
        price_logic_data = [
            {
                "form": f"http://testserver{self.form_url}",
                "json_logic_trigger": {
                    "invalid_op": [
                        {"var": "step1_textfield1"},
                        "hide step 1",
                    ]
                },
                "price": "123.15",
            }
        ]

        url = reverse(
            "api:form-price-logic-rules", kwargs={"uuid_or_slug": self.form.uuid}
        )
        response = self.client.put(url, data=price_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            response.json()["invalidParams"][0]["name"],
            "0.jsonLogicTrigger",
        )

    def test_invalid_price(self):
        self.client.force_authenticate(user=self.superuser)
        price_logic_data = [
            {
                "form": f"http://testserver{self.form_url}",
                "json_logic_trigger": {
                    "==": [
                        {"var": "step1_textfield1"},
                        "hide step 1",
                    ]
                },
                "price": "",
            }
        ]

        url = reverse(
            "api:form-price-logic-rules", kwargs={"uuid_or_slug": self.form.uuid}
        )
        response = self.client.put(url, data=price_logic_data)

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            response.json()["invalidParams"][0]["name"],
            "0.price",
        )
