from unittest.mock import patch

from django.test import TestCase

import requests_mock
from O365 import Account

from ..client import MSGraphClient
from ..exceptions import MSAuthenticationError
from .factories import MSGraphServiceFactory


# kill all requests
@requests_mock.Mocker(real_http=False)
class MSGraphClientTests(TestCase):
    def test_client_automatically_authenticates(self, m):
        service = MSGraphServiceFactory.create()

        with self.subTest("error"):
            with self.assertRaisesRegex(MSAuthenticationError, "cannot authenticate"):
                MSGraphClient(service)

        with self.subTest("authenticate"):
            with patch.object(Account, "authenticate", return_value=True):
                client = MSGraphClient(service)
                # no error!

        with self.subTest("is_authenticated"):
            with patch.object(Account, "is_authenticated", True):
                client = MSGraphClient(service)
                self.assertTrue(client.is_authenticated)
