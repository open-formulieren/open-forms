import io
import json
from unittest.mock import patch
from zipfile import ZipFile

from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from privates.test import temp_private_root

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.forms.admin.tasks import process_forms_export
from openforms.forms.models.form import FormsExport
from openforms.forms.tests.factories import FormFactory
from openforms.payments.contrib.ogone.constants import OgoneEndpoints
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory
from openforms.payments.contrib.worldline.constants import WorldlineEndpoints
from openforms.payments.contrib.worldline.models import WorldlineMerchant
from openforms.payments.contrib.worldline.tests.factories import (
    WorldlineMerchantFactory,
)
from openforms.utils.urls import build_absolute_uri


@disable_admin_mfa()
@override_settings(LANGUAGE_CODE="en")
class TestExportFormsView(WebTest):
    def test_not_staff_cant_access(self):
        user = UserFactory(is_staff=False, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(302, response.status_code)

    def test_staff_cant_access(self):
        user = StaffUserFactory()
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(403, response.status_code)

    def test_staff_with_right_permissions_can_access(self):
        user = StaffUserFactory(user_permissions=["forms.add_formsexport"])

        self.client.force_login(user)
        response = self.client.get(reverse("admin:forms_export"))

        self.assertEqual(200, response.status_code)

    def test_no_forms_uuids_specified(self):
        user = SuperUserFactory.create(email="test@email.nl")

        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        form = response.form
        submission_response = form.submit()

        # Doesn't redirect because there are errors
        self.assertEqual(200, submission_response.status_code)

    def test_wrong_form_uuids(self):
        user = SuperUserFactory.create(email="test@email.nl")

        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        form = response.form
        form["forms_uuids"] = "5cd503bf-e83f-4fd1-9acd-c2e8975ff65d"
        submission_response = form.submit()

        # Doesn't redirect because there are errors
        self.assertEqual(200, submission_response.status_code)

    @patch("openforms.forms.admin.views.process_forms_export.delay")
    def test_success_message(self, m):
        form = FormFactory.create()
        user = SuperUserFactory.create(email="test@email.nl")
        response = self.app.get(reverse("admin:forms_export"), user=user)

        self.assertEqual(200, response.status_code)

        page_form = response.form
        page_form["forms_uuids"] = str(form.uuid)
        submission_response = page_form.submit()

        self.assertRedirects(
            submission_response, reverse("admin:forms_form_changelist")
        )
        m.assert_called_with(forms_uuids=[form.uuid], user_id=user.id)

        submission_response = submission_response.follow()
        messages = list(submission_response.context.get("messages"))

        self.assertEqual(1, len(messages))
        self.assertEqual(messages[0].tags, "success")


@disable_admin_mfa()
@temp_private_root()
class TestDownloadExportFormView(TestCase):
    def test_not_logged_in_cant_access(self):
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": "1394a957-e1a5-41ab-91f5-c5f741f83622"},
            )
        )

        response = self.client.get(download_url)

        self.assertEqual(302, response.status_code)

    def test_not_superuser_cant_access(self):
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": "1394a957-e1a5-41ab-91f5-c5f741f83622"},
            )
        )

        user = UserFactory(is_staff=True, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(download_url)

        self.assertEqual(403, response.status_code)

    def test_staff_user_with_permissions_can_download(self):
        user = StaffUserFactory(
            email="test1@email.nl",
            user_permissions=["forms.view_formsexport"],
        )
        forms_export = FormsExport.objects.create(
            export_content=File(io.BytesIO(b"Some test content"), name="test.zip"),
            user=user,
        )
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": forms_export.uuid},
            )
        )

        self.client.force_login(user)
        response = self.client.get(download_url)

        self.assertEqual(response.status_code, 200)

    def test_wrong_export_gives_404(self):
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={
                    "uuid": "1394a957-e1a5-41ab-91f5-c5f741f83622"
                },  # Random non existent UUID
            )
        )

        user = SuperUserFactory.create(email="test@email.nl")
        self.client.force_login(user)
        response = self.client.get(download_url)

        self.assertEqual(404, response.status_code)

    def test_wrong_user_cant_download(self):
        user1 = SuperUserFactory(email="test1@email.nl")
        user2 = SuperUserFactory(email="test2@email.nl")
        forms_export = FormsExport.objects.create(
            export_content=File(io.BytesIO(b"Some test content"), name="test.zip"),
            user=user1,
        )
        download_url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": forms_export.uuid},
            )
        )

        self.client.force_login(user2)
        response = self.client.get(download_url)

        self.assertEqual(404, response.status_code)


@disable_admin_mfa()
@temp_private_root()
@override_settings(LANGUAGE_CODE="en")
class TestImportView(WebTest):
    def test_not_superuser_cant_access(self):
        user = UserFactory(is_staff=False, is_superuser=False)
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_import"))

        self.assertEqual(302, response.status_code)

    def test_no_form_add_permissions_cant_access(self):
        user = StaffUserFactory()
        self.client.force_login(user)

        self.assertEqual(0, user.user_permissions.count())

        response = self.client.get(reverse("admin:forms_import"))

        self.assertEqual(403, response.status_code)

    def test_form_add_permissions_can_access(self):
        user = StaffUserFactory(user_permissions=["forms.add_form"])
        self.client.force_login(user)

        response = self.client.get(reverse("admin:forms_import"))

        self.assertEqual(200, response.status_code)

    @patch("openforms.forms.admin.views.process_forms_import.delay")
    def test_bulk_import(self, m_bulk_import):
        form1, form2 = FormFactory.create_batch(2)
        user = SuperUserFactory.create(email="test@email.nl")

        process_forms_export(
            forms_uuids=[form1.uuid, form2.uuid],
            user_id=user.id,
        )

        form_export = FormsExport.objects.get()

        response = self.app.get(reverse("admin:forms_import"), user=user)

        self.assertEqual(200, response.status_code)

        html_form = response.form
        html_form["file"] = (
            "file.zip",
            form_export.export_content.read(),
        )
        submission_response = html_form.submit("_import")

        self.assertEqual(302, submission_response.status_code)
        m_bulk_import.assert_called()

        submission_response = submission_response.follow()
        messages = list(submission_response.context.get("messages"))

        self.assertEqual(1, len(messages))
        self.assertEqual(
            "The bulk import is being processed! The imported forms will soon be available.",
            messages[0].message,
        )

    @patch("openforms.forms.admin.views.import_form")
    def test_single_import(self, m_import):
        file = io.BytesIO()
        with ZipFile(file, mode="w") as zf:
            with zf.open("forms.json", "w") as f:
                f.write(
                    json.dumps(
                        [
                            {
                                "uuid": "b8315e1d-3134-476f-8786-7661d8237c51",
                                "name": "Form 000",
                                "internal_name": "Form internal",
                                "slug": "bed",
                                "product": None,
                                "authentication_backends": ["digid"],
                            }
                        ]
                    ).encode("utf-8")
                )

            with zf.open("formSteps.json", "w") as f:
                f.write(b"[]")

            with zf.open("formDefinitions.json", "w") as f:
                f.write(b"[]")

            with zf.open("formLogic.json", "w") as f:
                f.write(b"[]")

        user = SuperUserFactory.create()
        response = self.app.get(reverse("admin:forms_import"), user=user)

        self.assertEqual(200, response.status_code)

        html_form = response.form
        file.seek(0)
        html_form["file"] = (
            "file.zip",
            file.read(),
        )
        submission_response = html_form.submit("_import")

        self.assertEqual(302, submission_response.status_code)
        m_import.assert_called()

        submission_response = submission_response.follow()
        messages = list(submission_response.context.get("messages"))

        self.assertEqual(1, len(messages))
        self.assertEqual(
            "Form successfully imported!",
            messages[0].message,
        )


@disable_admin_mfa()
class TestMigrationForm(WebTest):
    csrf_checks = False

    def test_single_form(self):
        user = SuperUserFactory.create()
        ogone_merchant = OgoneMerchantFactory(
            label="Merchant Y", pspid="merchant-y", endpoint_preset=OgoneEndpoints.test
        )
        form_to_migrate = FormFactory(
            name="Ogone form 1",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant.pk},
        )

        response = self.app.post(
            reverse("admin:forms_payment_migration"),
            {"forms_to_migrate": [form_to_migrate.pk]},
            user=user,
        )

        self.assertRedirects(response, reverse("admin:forms_form_changelist"))

        worldline_merchant = WorldlineMerchant.objects.get()

        self.assertEqual(worldline_merchant.label, "Merchant Y")
        self.assertEqual(worldline_merchant.pspid, "merchant-y")
        self.assertEqual(worldline_merchant.endpoint, WorldlineEndpoints.test)

        form_to_migrate.refresh_from_db()

        self.assertEqual(form_to_migrate.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate.payment_backend_options, {"merchant": "merchant-y"}
        )

    def test_multiple_forms(self):
        user = SuperUserFactory.create()
        ogone_merchant_1 = OgoneMerchantFactory(
            label="Merchant Y", pspid="merchant-y", endpoint_preset=OgoneEndpoints.test
        )
        form_to_migrate_1 = FormFactory(
            name="Ogone form 1",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_1.pk},
        )
        ogone_merchant_2 = OgoneMerchantFactory(
            label="Merchant Z", pspid="merchant-z", endpoint_preset=OgoneEndpoints.live
        )
        form_to_migrate_2 = FormFactory(
            name="Ogone form 2",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_2.pk},
        )

        response = self.app.post(
            reverse("admin:forms_payment_migration"),
            {"forms_to_migrate": [form_to_migrate_1.pk, form_to_migrate_2.pk]},
            user=user,
        )

        self.assertRedirects(response, reverse("admin:forms_form_changelist"))

        worldline_merchants = WorldlineMerchant.objects.order_by("pspid")

        self.assertEqual(worldline_merchants[0].label, "Merchant Y")
        self.assertEqual(worldline_merchants[0].pspid, "merchant-y")
        self.assertEqual(worldline_merchants[0].endpoint, WorldlineEndpoints.test)
        self.assertEqual(worldline_merchants[1].label, "Merchant Z")
        self.assertEqual(worldline_merchants[1].pspid, "merchant-z")
        self.assertEqual(worldline_merchants[1].endpoint, WorldlineEndpoints.live)

        form_to_migrate_1.refresh_from_db()
        form_to_migrate_2.refresh_from_db()

        self.assertEqual(form_to_migrate_1.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate_1.payment_backend_options, {"merchant": "merchant-y"}
        )
        self.assertEqual(form_to_migrate_2.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate_2.payment_backend_options, {"merchant": "merchant-z"}
        )

    def test_reuse_merchants(self):
        user = SuperUserFactory.create()
        ogone_merchant_1 = OgoneMerchantFactory(
            label="Merchant Y", pspid="merchant-y", endpoint_preset=OgoneEndpoints.test
        )
        form_to_migrate_1 = FormFactory(
            name="Ogone form 1",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_1.pk},
        )
        ogone_merchant_2 = OgoneMerchantFactory(
            label="Merchant Z", pspid="merchant-z", endpoint_preset=OgoneEndpoints.live
        )
        form_to_migrate_2 = FormFactory(
            name="Ogone form 2",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_2.pk},
        )
        worldline_merchant = WorldlineMerchantFactory(
            label="Merchant A",
            pspid="merchant-z",
            endpoint=WorldlineEndpoints.test,
        )

        response = self.app.post(
            reverse("admin:forms_payment_migration"),
            {"forms_to_migrate": [form_to_migrate_1.pk, form_to_migrate_2.pk]},
            user=user,
        )

        self.assertRedirects(response, reverse("admin:forms_form_changelist"))

        new_merchant = WorldlineMerchant.objects.order_by("pspid").first()
        worldline_merchant.refresh_from_db()

        self.assertEqual(new_merchant.label, "Merchant Y")
        self.assertEqual(new_merchant.pspid, "merchant-y")
        self.assertEqual(new_merchant.endpoint, WorldlineEndpoints.test)
        self.assertEqual(worldline_merchant.label, "Merchant Z")
        self.assertEqual(worldline_merchant.pspid, "merchant-z")
        self.assertEqual(worldline_merchant.endpoint, WorldlineEndpoints.live)

        form_to_migrate_1.refresh_from_db()
        form_to_migrate_2.refresh_from_db()

        self.assertEqual(form_to_migrate_1.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate_1.payment_backend_options, {"merchant": "merchant-y"}
        )
        self.assertEqual(form_to_migrate_2.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate_2.payment_backend_options, {"merchant": "merchant-z"}
        )

    def test_non_existent_merchant(self):
        user = SuperUserFactory.create()
        ogone_merchant_1 = OgoneMerchantFactory(
            label="Merchant Y", pspid="merchant-y", endpoint_preset=OgoneEndpoints.test
        )
        form_to_migrate_1 = FormFactory(
            name="Ogone form 1",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_1.pk},
        )
        form_to_migrate_2 = FormFactory(
            name="Ogone form 2",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": 1000000000},
        )

        response = self.app.post(
            reverse("admin:forms_payment_migration"),
            {"forms_to_migrate": [form_to_migrate_1.pk, form_to_migrate_2.pk]},
            user=user,
        )

        self.assertContains(response, _("Please select a new merchant for these forms"))

        self.assertEqual(WorldlineMerchant.objects.count(), 0)

        form_to_migrate_1.refresh_from_db()
        form_to_migrate_2.refresh_from_db()

        self.assertEqual(form_to_migrate_1.payment_backend, "ogone-legacy")
        self.assertEqual(
            form_to_migrate_1.payment_backend_options,
            {"merchant_id": ogone_merchant_1.pk},
        )
        self.assertEqual(form_to_migrate_2.payment_backend, "ogone-legacy")
        self.assertEqual(
            form_to_migrate_2.payment_backend_options,
            {"merchant_id": 1000000000},
        )

    def test_migrate_credentials(self):
        user = SuperUserFactory.create()
        ogone_merchant_1 = OgoneMerchantFactory(
            label="Merchant Y",
            pspid="merchant-y",
            endpoint_preset=OgoneEndpoints.test,
            api_key="api-key-1",
            api_secret="api-secret-1",
        )
        form_to_migrate_1 = FormFactory(
            name="Ogone form 1",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_1.pk},
        )
        ogone_merchant_2 = OgoneMerchantFactory(
            label="Merchant Z",
            pspid="merchant-z",
            endpoint_preset=OgoneEndpoints.live,
            api_key="api-key-2",
            api_secret="api-secret-2",
        )
        form_to_migrate_2 = FormFactory(
            name="Ogone form 2",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_2.pk},
        )
        worldline_merchant = WorldlineMerchantFactory(
            label="Merchant A",
            pspid="merchant-z",
            endpoint=WorldlineEndpoints.test,
            api_key="existing-key",
            api_secret="existing-secret",
        )

        response = self.app.post(
            reverse("admin:forms_payment_migration"),
            {"forms_to_migrate": [form_to_migrate_1.pk, form_to_migrate_2.pk]},
            user=user,
        )

        self.assertRedirects(response, reverse("admin:forms_form_changelist"))

        new_merchant = WorldlineMerchant.objects.order_by("pspid").first()
        worldline_merchant.refresh_from_db()

        self.assertEqual(new_merchant.api_key, "api-key-1")
        self.assertEqual(new_merchant.api_secret, "api-secret-1")
        self.assertEqual(worldline_merchant.label, "Merchant Z")
        self.assertEqual(worldline_merchant.api_key, "api-key-2")
        self.assertEqual(worldline_merchant.api_secret, "api-secret-2")

    def test_migrate_com_attribute(self):
        user = SuperUserFactory.create()
        ogone_merchant_1 = OgoneMerchantFactory(
            label="Merchant Y", pspid="merchant-y", endpoint_preset=OgoneEndpoints.test
        )
        form_to_migrate_1 = FormFactory(
            name="Ogone form 1",
            payment_backend="ogone-legacy",
            payment_backend_options={
                "merchant_id": ogone_merchant_1.pk,
                "com_template": "{{ foo }}",
            },
        )
        ogone_merchant_2 = OgoneMerchantFactory(
            label="Merchant Z", pspid="merchant-z", endpoint_preset=OgoneEndpoints.live
        )
        form_to_migrate_2 = FormFactory(
            name="Ogone form 2",
            payment_backend="ogone-legacy",
            payment_backend_options={"merchant_id": ogone_merchant_2.pk},
        )

        response = self.app.post(
            reverse("admin:forms_payment_migration"),
            {"forms_to_migrate": [form_to_migrate_1.pk, form_to_migrate_2.pk]},
            user=user,
        )

        self.assertRedirects(response, reverse("admin:forms_form_changelist"))

        form_to_migrate_1.refresh_from_db()
        form_to_migrate_2.refresh_from_db()

        self.assertEqual(form_to_migrate_1.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate_1.payment_backend_options,
            {"merchant": "merchant-y", "descriptor_template": "{{ foo }}"},
        )
        self.assertEqual(form_to_migrate_2.payment_backend, "worldline")
        self.assertEqual(
            form_to_migrate_2.payment_backend_options, {"merchant": "merchant-z"}
        )
