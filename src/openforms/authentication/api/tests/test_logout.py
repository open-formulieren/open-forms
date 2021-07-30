from unittest.mock import patch

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.authentication.constants import AuthAttribute
from openforms.authentication.registry import Registry
from openforms.authentication.tests.test_registry import Plugin


class LogoutTest(APITestCase):
    def test_logout(self):
        register = Registry()

        register("plugin1")(Plugin)
        plugin1 = register["plugin1"]
        plugin1.provides_auth = AuthAttribute.bsn

        register("plugin2")(Plugin)
        plugin2 = register["plugin2"]
        plugin2.provides_auth = AuthAttribute.kvk

        session = self.client.session
        session[AuthAttribute.bsn] = "123456789"
        session[AuthAttribute.kvk] = "987654321"
        session.save()

        self.assertIn(AuthAttribute.bsn, self.client.session)
        self.assertIn(AuthAttribute.kvk, self.client.session)

        with patch("openforms.authentication.views.register", register) as m:
            response = self.client.delete(reverse("api:logout"))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertNotIn(AuthAttribute.bsn, self.client.session)
        self.assertNotIn(AuthAttribute.kvk, self.client.session)
