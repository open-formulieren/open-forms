from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.variables.constants import FormVariableDataTypes, FormVariableSources


class KlantinteractiesOptionsTests(APITestCase):
    def test_plugin_options_validation(self):
        user = SuperUserFactory.create()
        form = FormFactory.create()
        form_step = FormStepFactory.create(form=form)
        form_definition = form_step.form_definition
        form_path = reverse("api:form-detail", kwargs={"uuid_or_slug": form.uuid})
        form_url = f"http://testserver.com{form_path}"
        form_definition_path = reverse(
            "api:formdefinition-detail", kwargs={"uuid": form_definition.uuid}
        )
        form_definition_url = f"http://testserver.com{form_definition_path}"
        data = {
            "form": form_url,
            "form_definition": form_definition_url,
            "key": "userdefined",
            "name": "klantinteracties-prefill",
            "service_fetch_configuration": None,
            "data_type": FormVariableDataTypes.string,
            "source": FormVariableSources.user_defined,
            "prefill_plugin": "klantinteracties",
            "prefill_attribute": "",
            "prefill_options": {"email": True, "phone_number": True},
        }
        prefill_options_valid = [
            {"email": True, "phone_number": True},
            {"email": True, "phone_number": False},
            {"email": False, "phone_number": True},
        ]
        prefill_options_invalid = [{"email": False, "phone_number": False}]

        self.client.force_authenticate(user)

        for prefill_options in prefill_options_valid:
            with self.subTest(prefill_options=prefill_options):
                response = self.client.put(
                    reverse(
                        "api:form-variables",
                        kwargs={"uuid_or_slug": form.uuid},
                    ),
                    data=[{**data, **{"prefill_options": prefill_options}}],
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)

        for prefill_options in prefill_options_invalid:
            with self.subTest(prefill_options=prefill_options):
                response = self.client.put(
                    reverse(
                        "api:form-variables",
                        kwargs={"uuid_or_slug": form.uuid},
                    ),
                    data=[{**data, **{"prefill_options": prefill_options}}],
                )

                self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
                self.assertEqual(
                    response.json()["invalidParams"],
                    [
                        {
                            "name": "0.prefillOptions.nonFieldErrors",
                            "code": "invalid",
                            "reason": _(
                                "You must enable at least one digital address type."
                            ),
                        }
                    ],
                )
