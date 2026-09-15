from .factories import CustomerInteractionsAPIGroupConfigFactory
from .typing import ExpectedDigitalAddress


class CustomerInteractionsMixin:
    """
    Mixin to use Customer Interactions API in unit tests
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()  # pyright: ignore[reportAttributeAccessIssue]

        cls.config = CustomerInteractionsAPIGroupConfigFactory.create(
            for_test_docker_compose=True
        )

    def assertAddressPresent(self, results, expected_address: ExpectedDigitalAddress):
        matches = [
            result
            for result in results
            if all(
                result.get(key) == expected_value
                for key, expected_value in expected_address.items()
            )
        ]

        self.assertEqual(  # pyright: ignore[reportAttributeAccessIssue]
            len(matches),
            1,
            f"Expected exactly one matching address: {expected_address['adres']}",
        )

        results.remove(matches[0])
