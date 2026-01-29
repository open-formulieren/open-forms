from django.templatetags.static import static
from django.urls import reverse

from django_webtest import TransactionWebTest, WebTest
from furl import furl
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)

from ..models import TranslationsMetaData
from .factories import TranslationsMetaDataFactory


@disable_admin_mfa()
class AdminLanguageDecouplingTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()

    def test_language_cookie_ignored_by_admin(self):
        # sets the language cookie
        _response = self.app.put_json(reverse("api:i18n:language"), {"code": "en"})
        assert _response.headers["Content-Language"] == "en"
        assert self.app.cookies["openforms_language"] == "en"

        admin_index = self.app.get(
            reverse("admin:index"),
            headers={"Accept-Language": "nl-NL, nl;q=0.9, en;q=0.5"},
            user=self.user,
        )

        self.assertEqual(admin_index["Content-Language"], "nl")

    def test_user_preference_overrides_browser_prefs(self):
        self.user.ui_language = "en"
        self.user.save()

        admin_index = self.app.get(
            reverse("admin:index"),
            headers={"Accept-Language": "nl-NL, nl;q=0.9, en;q=0.5"},
            user=self.user,
        )

        self.assertEqual(admin_index["Content-Language"], "en")


@disable_admin_mfa()
class AdminTranslationMetaDataTests(WebTest):
    def test_changelist_page_access(self):
        user = UserFactory.create(is_staff=False, is_superuser=False)
        super_but_not_staff = SuperUserFactory.create(is_staff=False)
        staff_user = StaffUserFactory.create()
        super_user = SuperUserFactory.create()

        url = reverse("admin:of_translations_translationsmetadata_changelist")

        with self.subTest("simple user"):
            response = self.app.get(url, user=user)

            expected_redirect = furl(reverse("admin:login")).set({"next": str(url)})
            self.assertRedirects(
                response, str(expected_redirect), target_status_code=302
            )

        with self.subTest("super user but not staff"):
            response = self.app.get(url, user=super_but_not_staff)

            expected_redirect = furl(reverse("admin:login")).set({"next": str(url)})
            self.assertRedirects(
                response, str(expected_redirect), target_status_code=302
            )

        with self.subTest("staff user"):
            response = self.app.get(url, user=staff_user, status=403)

        self.assertEqual(response.status_code, 403)

        with self.subTest("power/super user"):
            response = self.app.get(url, user=super_user)

            self.assertEqual(response.status_code, 200)

    def test_change_page_access(self):
        translation_metadata = TranslationsMetaDataFactory.create()
        user = UserFactory.create(is_staff=False, is_superuser=False)
        super_but_not_staff = SuperUserFactory.create(is_staff=False)
        staff_user = StaffUserFactory.create()
        super_user = SuperUserFactory.create()

        url = reverse(
            "admin:of_translations_translationsmetadata_change",
            kwargs={"object_id": translation_metadata.pk},
        )

        with self.subTest("simple user"):
            response = self.app.get(url, user=user)

            expected_redirect = furl(reverse("admin:login")).set({"next": str(url)})
            self.assertRedirects(
                response, str(expected_redirect), target_status_code=302
            )

        with self.subTest("super user but not staff"):
            response = self.app.get(url, user=super_but_not_staff)

            expected_redirect = furl(reverse("admin:login")).set({"next": str(url)})
            self.assertRedirects(
                response, str(expected_redirect), target_status_code=302
            )

        with self.subTest("staff user"):
            response = self.app.get(url, user=staff_user, status=403)

        self.assertEqual(response.status_code, 403)

        with self.subTest("power/super user"):
            response = self.app.get(url, user=super_user)

            self.assertEqual(response.status_code, 200)

    def test_default_messages_download_link_with_instance_saved(self):
        super_user = SuperUserFactory.create()
        translation_metadata = TranslationsMetaDataFactory.create()

        link = static(f"sdk/i18n/messages/{translation_metadata.language_code}.json")
        response = self.app.get(
            reverse("admin:of_translations_translationsmetadata_changelist"),
            user=super_user,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(link, response.text)

    def test_default_messages_download_link_during_creation_of_instance(self):
        super_user = SuperUserFactory.create()
        translation_metadata = TranslationsMetaDataFactory.build()

        link = static(f"sdk/i18n/messages/{translation_metadata.language_code}.json")
        response = self.app.get(
            reverse("admin:of_translations_translationsmetadata_changelist"),
            user=super_user,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(link, response.text)

    def test_default_messages_download_link_during_creation_of_instance_and_language_missing(
        self,
    ):
        super_user = SuperUserFactory.create()
        translation_metadata = TranslationsMetaDataFactory.build()
        translation_metadata.language_code = ""
        translation_metadata.save()

        link = static(f"sdk/i18n/messages/{translation_metadata.language_code}.json")
        response = self.app.get(
            reverse("admin:of_translations_translationsmetadata_changelist"),
            user=super_user,
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(link, response.text)

    def test_compiled_asset_download_link_with_instance_saved(self):
        super_user = SuperUserFactory.create()
        translation_metadata = TranslationsMetaDataFactory.create(
            with_compiled_asset=True
        )

        response = self.app.get(
            reverse(
                "admin:of_translations_translationsmetadata_change",
                kwargs={"object_id": translation_metadata.pk},
            ),
            user=super_user,
        )

        asset_url = reverse(
            "admin:of_translations_translationsmetadata_compiled_asset",
            args=[translation_metadata.pk],
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(asset_url, response.text)

    def test_compiled_asset_download_link_with_no_asset(self):
        super_user = SuperUserFactory.create()
        translation_metadata = TranslationsMetaDataFactory.create()

        response = self.app.get(
            reverse(
                "admin:of_translations_translationsmetadata_change",
                kwargs={"object_id": translation_metadata.pk},
            ),
            user=super_user,
        )

        asset_url = reverse(
            "admin:of_translations_translationsmetadata_compiled_asset",
            args=[translation_metadata.pk],
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(asset_url, response.text)


@disable_admin_mfa()
class AdminTranslationMetaDataTransactionTests(TransactionWebTest):
    def test_saving_model(self):
        super_user = SuperUserFactory.create()

        response = self.app.get(
            reverse("admin:of_translations_translationsmetadata_add"), user=super_user
        )
        form = response.forms["translationsmetadata_form"]

        form["language_code"] = "nl"
        form["messages_file"] = (
            "test.json",
            b"""{
            "skjd8uh": {
                "defaultMessage": "A modified translated text",
                "description": "A description",
                "originalDefault": "Completed"
            }
            }""",
            "application/json",
        )
        form.submit().follow()

        expected_messages_file_data = b'{\n            "skjd8uh": {\n                "defaultMessage": "A modified translated text",\n                "description": "A description",\n                "originalDefault": "Completed"\n            }\n            }'
        expected_compiled_asset_data = b'{\n  "skjd8uh": [\n    {\n      "type": 0,\n      "value": "A modified translated text"\n    }\n  ]\n}\n'

        obj = TranslationsMetaData.objects.get()

        self.assertEqual(obj.language_code, "nl")
        self.assertEqual(obj.messages_file.file.read(), expected_messages_file_data)
        self.assertEqual(obj.compiled_asset.file.read(), expected_compiled_asset_data)
