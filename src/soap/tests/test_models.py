from django.test import SimpleTestCase

from hypothesis import given, strategies as st

from .factories import SoapServiceFactory


class ModelTests(SimpleTestCase):
    @given(st.text(min_size=1))
    def test_string_representation(self, label):
        service = SoapServiceFactory.build(label=label)

        self.assertEqual(str(service), label)
