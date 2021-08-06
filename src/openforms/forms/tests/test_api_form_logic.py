from django.http import HttpRequest
from django.urls import reverse

from furl import furl
from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.models.form import FormLogic
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.tests.form_logic.factories import FormLogicFactory


class FormLogicAPITests(APITestCase):
    def test_auth_required(self):
        url = reverse("api:form-logics-list")

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_list_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form1 = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form1,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )
        form2 = FormFactory.create()
        step2 = FormStepFactory.create(
            form=form2,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2_textfield1",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form_step=step2,
            component="step2_textfield1",
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 2",
                ]
            },
            actions=[
                {
                    "name": "Hide element",
                    "type": "property",
                    "property": {
                        "value": "hidden",
                    },
                    "state": True,
                }
            ],
        )
        FormLogicFactory.create(
            form_step=step1,
            component="step1_textfield1",
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            actions=[
                {
                    "name": "Hide element",
                    "type": "property",
                    "property": {
                        "value": "hidden",
                    },
                    "state": True,
                }
            ],
        )

        force_authenticate(user)
        url = reverse("api:form-logics-list")
        url = furl(url).set({"form": form1.uuid}).url
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_data = response.json()

        self.assertEqual(1, len(response_data))

    def test_create_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )

        form_version_data = {
            "form_step": f"http://testserver{reverse('api:form-steps-detail', kwargs={'form_uuid_or_slug': form.uuid, 'uuid': step.uuid})}",
            "component": "step1_textfield1",
            "json_logic_trigger": {
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            "actions": [
                {
                    "name": "Hide element",
                    "type": "property",
                    "property": {
                        "value": "hidden",
                    },
                    "state": True,
                }
            ],
        }

        self.client.login(
            request=HttpRequest(), username=user.username, password="test"
        )
        url = reverse("api:form-logics-list")
        response = self.client.post(url, data=form_version_data)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        form_logics_qs = FormLogic.objects.all()

        self.assertEqual(1, form_logics_qs.count())

        form_logic = form_logics_qs.get()

        self.assertEqual(step, form_logic.form_step)

    def test_partial_update_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        step1 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )
        step2 = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step2_textfield1",
                    }
                ]
            },
        )
        logic = FormLogicFactory.create(
            form_step=step1,
            component="step1_textfield1",
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 2",
                ]
            },
            actions=[
                {
                    "name": "Hide element",
                    "type": "property",
                    "property": {
                        "value": "hidden",
                    },
                    "state": True,
                }
            ],
        )

        self.client.login(
            request=HttpRequest(), username=user.username, password="test"
        )
        url = reverse("api:form-logics-detail", kwargs={"uuid": logic.uuid})
        response = self.client.patch(
            url,
            data={
                "form_step": f"http://testserver{reverse('api:form-steps-detail', kwargs={'form_uuid_or_slug': form.uuid, 'uuid': step2.uuid})}"
            },
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        logic.refresh_from_db()

        self.assertEqual(step2, logic.form_step)

    def test_delete_form_logic(self):
        user = SuperUserFactory.create(username="test", password="test")
        form = FormFactory.create()
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "step1_textfield1",
                    }
                ]
            },
        )

        logic = FormLogicFactory.create(
            form_step=step,
            component="step1_textfield1",
            json_logic_trigger={
                "==": [
                    {"var": "step1_textfield1"},
                    "hide step 1",
                ]
            },
            actions=[
                {
                    "name": "Hide element",
                    "type": "property",
                    "property": {
                        "value": "hidden",
                    },
                    "state": True,
                }
            ],
        )

        self.client.login(
            request=HttpRequest(), username=user.username, password="test"
        )
        url = reverse("api:form-logics-detail", kwargs={"uuid": logic.uuid})
        response = self.client.delete(url)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(0, FormLogic.objects.all().count())
