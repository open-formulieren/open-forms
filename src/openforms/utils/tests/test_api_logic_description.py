from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory


class LogicDescriptionEndpointTests(APITestCase):
    endpoint = reverse_lazy("api:generate-logic-description")

    def test_auth_required(self):
        with self.subTest("anon user"):
            response = self.client.post(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        with self.subTest("non-staff user"):
            user = UserFactory.create(is_staff=False)
            self.client.force_authenticate(user=user)

            response = self.client.post(self.endpoint)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        with self.subTest("authenticated staff user"):
            staff_user = StaffUserFactory.create()
            self.client.force_authenticate(user=staff_user)

            response = self.client.post(self.endpoint)

            self.assertNotIn(
                response.status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
            )

    def test_valid_expressions_generate_descriptions(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        expressions = (
            # simple expression
            {"==": [{"var": "foo"}, "bar"]},
            # nested expression
            {
                "!": [
                    {
                        "and": [
                            {"+": [3, {"var": ["bar"]}]},
                            {"!!": {"var": "foo"}},
                        ]
                    }
                ]
            },
            # embedded _meta.description bits
            {"==": [1, 1], "_meta": {"description": "identity"}},
        )

        for expression in expressions:
            with self.subTest(expression=expression):
                response = self.client.post(self.endpoint, {"expression": expression})

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                description = response.json()["description"]
                self.assertIsInstance(description, str)
                self.assertNotEqual(description, "")

    def test_invalid_expressions_are_detected(self):
        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        invalid_expressions = (
            {"==": [1], "+": [1, 2]},
            {"operator-that-should-not-exist": [{"var": "foo"}]},
        )

        for expression in invalid_expressions:
            with self.subTest(expression=expression):
                response = self.client.post(self.endpoint, {"expression": expression})

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                errors = {
                    param["name"]: param for param in response.json()["invalidParams"]
                }
                self.assertIn("expression", errors)
                self.assertEqual(errors["expression"]["code"], "invalid")
