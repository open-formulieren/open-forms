from django.test import TestCase

from stuf.tests.factories import SoapServiceFactory


class SoapServiceTest(TestCase):
    def test_factory(self):
        SoapServiceFactory.create()
