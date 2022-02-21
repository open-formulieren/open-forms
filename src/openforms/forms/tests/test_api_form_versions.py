import datetime

from django.urls import reverse

from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import StaffUserFactory, UserFactory

from ...submissions.tests.form_logic.factories import FormLogicFactory
from ..models import FormDefinition, FormLogic, FormStep, FormVersion
from .factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
    FormVersionFactory,
)
from .utils import EXPORT_BLOB


class FormVersionSaveAPITests(APITestCase):
    def test_auth_required(self):
        form = FormFactory.create()
        url = reverse("api:form-versions-list", args=(form.uuid,))

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_staff_required(self):
        # add the permissions to verify we specifically check is_staff
        user = UserFactory.create(
            is_staff=False, user_permissions=["change_form", "view_form"]
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

        versions = FormVersion.objects.filter(form=form)

        self.assertEqual(0, versions.count())

        url = reverse("api:form-versions-list", args=(form.uuid,))
        response = self.client.post(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @freeze_time("2020-12-11T10:53:19+01:00")
    def test_save_version(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)
        self.assertEqual(user.user_permissions.all().count(), 1)

        form = FormFactory.create()

        versions = FormVersion.objects.filter(form=form)

        self.assertEqual(0, versions.count())

        url = reverse("api:form-versions-list", args=(form.uuid,))
        response = self.client.post(url)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        versions = FormVersion.objects.filter(form=form)

        self.assertEqual(1, versions.count())

        version = versions.first()

        self.assertEqual(form, version.form)
        self.assertEqual(
            datetime.datetime.strptime(
                "2020-12-11T10:53:19+01:00", "%Y-%m-%dT%H:%M:%S%z"
            ),
            version.created,
        )

    def test_list_versions(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        form_1 = FormFactory.create()
        form_2 = FormFactory.create()

        FormVersionFactory.create(form=form_1)
        FormVersionFactory.create(form=form_2)

        self.assertEqual(2, FormVersion.objects.all().count())

        url = reverse("api:form-versions-list", args=(form_1.uuid,))
        response = self.client.get(url)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.data))


class FormVersionRestoreAPITests(APITestCase):
    def test_auth_required(self):
        form = FormFactory.create()
        form_version = FormVersionFactory.create(form=form)
        url = reverse(
            "api:form-versions-restore",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": form_version.uuid},
        )

        response = self.client.post(url)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_must_be_staff_user(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        form = FormFactory.create()
        form_version = FormVersionFactory.create(form=form)

        url = reverse(
            "api:form-versions-restore",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": form_version.uuid},
        )
        response = self.client.post(url)

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_restore_version(self):
        user = StaffUserFactory.create(user_permissions=["change_form"])
        self.client.force_authenticate(user=user)

        form_definition = FormDefinitionFactory.create(
            slug="test-definition-2", configuration={"test": "2"}
        )
        form = FormFactory.create(name="Test Form 2")
        FormStepFactory.create(form=form, form_definition=form_definition)
        FormLogicFactory.create(form=form)

        version = FormVersion.objects.create(
            form=form,
            created=datetime.datetime(2021, 7, 21, 12, 00, 00),
            export_blob=EXPORT_BLOB,
        )

        url = reverse(
            "api:form-versions-restore",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": version.uuid},
        )

        self.assertEqual(1, FormVersion.objects.all().count())
        self.assertEqual(1, FormDefinition.objects.all().count())

        response = self.client.post(url, data={"uuid": str(version.uuid)})

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        form.refresh_from_db()

        self.assertEqual(
            2, FormVersion.objects.count()
        )  # restore creates its own FormVersion
        self.assertEqual("Test Form 1", form.name)
        self.assertEqual("Test Form Internal 1", form.internal_name)
        self.assertEqual(2, FormDefinition.objects.all().count())

        form_steps = FormStep.objects.filter(form=form)
        form_logic = FormLogic.objects.filter(form=form)

        self.assertEqual(1, form_steps.count())
        self.assertEqual(1, form_logic.count())

        restored_form_definition = form_steps.get().form_definition

        self.assertEqual("Test Definition 1", restored_form_definition.name)
        self.assertEqual(
            "Test Definition Internal 1", restored_form_definition.internal_name
        )
        self.assertEqual("test-definition-1", restored_form_definition.slug)
        self.assertEqual(
            {"components": [{"key": "test", "test": "1"}]},
            restored_form_definition.configuration,
        )
