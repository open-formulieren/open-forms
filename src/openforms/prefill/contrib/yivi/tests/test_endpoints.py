from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory
from openforms.authentication.tests.factories import AttributeGroupFactory


class YiviPrefillPluginEndpointTests(APITestCase):
    attributes_endpoint = reverse_lazy("api:prefill_yivi:yivi-prefill-attributes-list")
    default_attributes_endpoint = reverse_lazy(
        "api:prefill-attribute-list", kwargs={"plugin": "yivi"}
    )

    def test_default_prefill_attributes_endpoint(self):
        AttributeGroupFactory.create(
            name="attribute-group1",
            uuid="50b0c4c0-16e6-4866-8d0d-05914c2161b8",
            attributes=[
                "irma-demo.gemeente.personalData.fullname",
                "irma-demo.gemeente.personalData.dateofbirth",
            ],
        )

        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.default_attributes_endpoint)

        # Expect that the default attributes endpoint is available, and returns an empty
        # list
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_yivi_attributes_endpoint_auth_required(self):
        response = self.client.get(self.attributes_endpoint)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_yivi_attributes_endpoint_response(self):
        # Create test data
        AttributeGroupFactory.create(
            name="attribute-group1",
            uuid="50b0c4c0-16e6-4866-8d0d-05914c2161b8",
            attributes=[
                "irma-demo.gemeente.personalData.fullname",
                "irma-demo.gemeente.personalData.dateofbirth",
            ],
        )
        AttributeGroupFactory.create(
            name="attribute-group2",
            uuid="9d4a3849-73bd-4915-a3ca-0607605d31cf",
            attributes=["irma-demo.gemeente.personalData.over18"],
        )

        staff_user = StaffUserFactory.create()
        self.client.force_authenticate(user=staff_user)

        response = self.client.get(self.attributes_endpoint)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # The Yivi prefill attributes endpoint should return all defined attributeGroups,
        # and additional static attributes for retrieving identifier and loa values.
        expected = [
            {
                "attribute_group_uuid": "50b0c4c0-16e6-4866-8d0d-05914c2161b8",
                "attributes": [
                    {
                        "label": "irma-demo.gemeente.personalData.fullname",
                        "value": "additional_claims.irma-demo_gemeente_personalData_fullname",
                    },
                    {
                        "label": "irma-demo.gemeente.personalData.dateofbirth",
                        "value": "additional_claims.irma-demo_gemeente_personalData_dateofbirth",
                    },
                ],
                "is_static": False,
            },
            {
                "attribute_group_uuid": "9d4a3849-73bd-4915-a3ca-0607605d31cf",
                "attributes": [
                    {
                        "label": "irma-demo.gemeente.personalData.over18",
                        "value": "additional_claims.irma-demo_gemeente_personalData_over18",
                    },
                ],
                "is_static": False,
            },
            {
                "attribute_group_uuid": "00000000-0000-0000-0000-000000000000",
                "attributes": [
                    {
                        "label": _("Identifier"),
                        "value": "value",
                    },
                    {
                        "label": _("Level of Assurance"),
                        "value": "loa",
                    },
                ],
                "is_static": True,
            },
        ]
        self.assertEqual(response.data, expected)
