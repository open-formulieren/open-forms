from django.test import TestCase, tag
from django.utils.translation import gettext_lazy as _

from openforms.contrib.customer_interactions.tests.factories import (
    CustomerInteractionsAPIGroupConfigFactory,
)
from openforms.forms.tests.factories import FormFactory

from ..config import CommunicationPreferencesSerializer


class CommunicationPreferencesOptionsTests(TestCase):
    @tag("gh-5872")
    def test_prefill_options_incorrect_profile_variable(self):
        customer_interactions_config = (
            CustomerInteractionsAPIGroupConfigFactory.create()
        )
        form = FormFactory.create(
            generate_minimal_setup=True,
            formstep__form_definition__configuration={
                "components": [
                    {
                        "key": "profileNew",
                        "type": "customerProfile",
                        "label": "Profile",
                        "digitalAddressTypes": ["email"],
                        "shouldUpdateCustomerData": True,
                    }
                ],
            },
        )
        data = {
            "customer_interactions_api_group": customer_interactions_config.identifier,
            "profile_form_variable": "profileOld",
        }
        serializer = CommunicationPreferencesSerializer(
            data=data, context={"form": form}
        )

        is_valid = serializer.is_valid()

        self.assertFalse(is_valid)

        error = serializer.errors["profile_form_variable"][0]
        self.assertEqual(error.code, "invalid")
        self.assertEqual(
            error,
            _("No form variable with key '{key}' exists in the form.").format(
                key="profileOld"
            ),
        )
