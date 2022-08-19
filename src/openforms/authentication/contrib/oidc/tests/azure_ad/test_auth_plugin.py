from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import UserFactory


class AzureADOIDCAuthPluginEndpointTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = UserFactory.create(is_staff=True)

    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.user)

    # TODO
    ...
