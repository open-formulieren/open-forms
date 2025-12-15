
from .factories import CustomerInteractionsAPIGroupConfigFactory
from .typing import ExpectedDigitalAddress


class CustomerInteractionsMixin:
    """
    Mixin to use Customer Interactions API in unit tests
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.config = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def assertAddressPresent(self, results, expected_address: ExpectedDigitalAddress):
        adres = expected_address["adres"]
        found_address = next((da for da in results if da["adres"] == adres), None)
        for property, expected_value in expected_address.items():
            self.assertEqual(
                expected_value, found_address[property], f"for address {adres}"
            )
