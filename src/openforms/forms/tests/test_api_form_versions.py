from datetime import UTC, datetime

from django.urls import reverse

import time_machine
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory
from openforms.formio.tests.assertions import FormioMixin

from ..models import FormVersion
from .factories import (
    FormFactory,
    FormLogicFactory,
    FormVersionFactory,
)


class FormVersionSaveAPITests(APITestCase):
    def test_auth_required(self):
        form = FormFactory.create()
        url = reverse("api:form-versions-list", args=(form.uuid,))

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["forms.change_form", "forms.view_form"]
        )
        self.client.force_authenticate(user=user)
        form = FormFactory.create()
        url = reverse("api:form-versions-list", args=(form.uuid,))

        response = self.client.post(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_must_have_permission(self):
        user = StaffUserFactory.create()
        self.client.force_authenticate(user=user)
        form = FormFactory.create()
        url = reverse("api:form-versions-list", args=(form.uuid,))

        response = self.client.post(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @time_machine.travel("2020-12-11T10:53:19+01:00", tick=False)
    def test_save_version(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_authenticate(user=user)
        self.assertEqual(user.user_permissions.all().count(), 1)
        form = FormFactory.create()
        versions = FormVersion.objects.filter(form=form)
        assert not versions.exists()
        url = reverse("api:form-versions-list", args=(form.uuid,))

        response = self.client.post(url)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        version = FormVersion.objects.get()
        self.assertEqual(form, version.form)
        self.assertEqual(version.created, datetime(2020, 12, 11, 9, 53, 19, tzinfo=UTC))

    def test_list_versions(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_authenticate(user=user)
        form_1, form_2 = FormFactory.create_batch(2)
        FormVersionFactory.create(form=form_1)
        FormVersionFactory.create(form=form_2)
        url = reverse("api:form-versions-list", args=(form_1.uuid,))

        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data), 1)  # filtered by the form from the UUID


class FormVersionRestoreAPITests(FormioMixin, APITestCase):
    def test_auth_required(self):
        form_version = FormVersionFactory.create()
        url = reverse(
            "api:form-versions-restore",
            kwargs={
                "form_uuid_or_slug": form_version.form.uuid,
                "uuid": form_version.uuid,
            },
        )

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_must_be_staff_user(self):
        user = UserFactory.create(
            user_permissions=["forms.change_form"], is_staff=False
        )
        self.client.force_authenticate(user=user)
        form_version = FormVersionFactory.create()
        url = reverse(
            "api:form-versions-restore",
            kwargs={
                "form_uuid_or_slug": form_version.form.uuid,
                "uuid": form_version.uuid,
            },
        )

        response = self.client.post(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_restore_version_reverts_from_export_blobs(self):
        user = StaffUserFactory.create(user_permissions=["forms.change_form"])
        self.client.force_authenticate(user=user)

        # set up a form and create a version for it to restore
        form = FormFactory.create(
            generate_minimal_setup=True,
            slug="original-form-slug",
            formstep__slug="original-step-slug",
            formstep__form_definition__slug="original-fd-slug",
            formstep__form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "originalTextfield",
                        "label": "original text field",
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form, is_advanced=True, json_logic_trigger=True, actions=[]
        )
        form_version = FormVersionFactory.create(form=form)
        # apply modifications to revert with the restore
        form.slug = "modified-slug"
        form.save()
        step = form.formstep_set.get()
        step.slug = "modified-slug"
        step.save()
        step.form_definition.slug = "modified-fd-slug"
        step.form_definition.configuration = {"components": []}
        step.form_definition.save()
        form.formlogic_set.all().delete()
        # prepare restore
        url = reverse(
            "api:form-versions-restore",
            kwargs={
                "form_uuid_or_slug": form_version.form.uuid,
                "uuid": form_version.uuid,
            },
        )

        # do the restore
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        form.refresh_from_db()
        # restore creates its own FormVersion
        self.assertEqual(FormVersion.objects.count(), 2)

        self.assertEqual(form.slug, "original-form-slug")
        step = form.formstep_set.get()
        self.assertEqual(step.slug, "original-step-slug")
        self.assertEqual(step.form_definition.slug, "original-fd-slug")
        self.assertFormioComponent(
            step.form_definition.configuration,
            "originalTextfield",
            {
                "type": "textfield",
                "label": "original text field",
            },
        )
        self.assertEqual(form.formlogic_set.count(), 1)
