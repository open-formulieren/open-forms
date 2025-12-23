from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.utils.tests.vcr import OFVCRMixin

from .factories import ObjectsAPIGroupConfigFactory


@disable_admin_mfa()
class ObjectsAPIGroupConfigAdminTest(OFVCRMixin, WebTest):
    def test_name(self):
        ObjectsAPIGroupConfigFactory.create(name="test group")
        user = SuperUserFactory.create()

        response = self.app.get(
            reverse("admin:objects_api_objectsapigroupconfig_changelist"),
            user=user,
        )

        table = response.html.find("table", {"id": "result_list"})
        row = table.find("tbody").find("tr")

        self.assertEqual(row.find("th").string, "test group")

    def test_configure_catalogue(self):
        user = SuperUserFactory.create()
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        change_url = reverse(
            "admin:objects_api_objectsapigroupconfig_change",
            args=(api_group.pk,),
        )

        change_page = self.app.get(change_url, user=user)
        change_form = change_page.forms["objectsapigroupconfig_form"]
        change_form["catalogue_domain"] = "TEST"
        change_form["catalogue_rsin"] = "000000000"

        response = change_form.submit()
        assert response.status_code == 302

        api_group.refresh_from_db()
        self.assertEqual(api_group.catalogue_domain, "TEST")
        self.assertEqual(api_group.catalogue_rsin, "000000000")

    def test_partial_catalogue_configuration_displays_validation_errors(self):
        user = SuperUserFactory.create()
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        change_url = reverse(
            "admin:objects_api_objectsapigroupconfig_change",
            args=(api_group.pk,),
        )
        expected_error = _(
            "You must specify both domain and RSIN to uniquely identify a catalogue.",
        )

        with self.subTest("only domain specified"):
            change_page = self.app.get(change_url, user=user)
            change_form = change_page.forms["objectsapigroupconfig_form"]
            change_form["catalogue_domain"] = "TEST"

            response = change_form.submit()

            assert response.status_code == 200
            self.assertContains(response, expected_error)

        with self.subTest("only rsin specified"):
            change_page = self.app.get(change_url, user=user)
            change_form = change_page.forms["objectsapigroupconfig_form"]
            change_form["catalogue_rsin"] = "000000000"

            response = change_form.submit()

            assert response.status_code == 200
            self.assertContains(response, expected_error)

    def test_configure_catalogue_that_doesnt_exist(self):
        user = SuperUserFactory.create()
        api_group = ObjectsAPIGroupConfigFactory.create(
            for_test_docker_compose=True,
            catalogue_domain="",
            catalogue_rsin="",
        )
        change_url = reverse(
            "admin:objects_api_objectsapigroupconfig_change",
            args=(api_group.pk,),
        )

        change_page = self.app.get(change_url, user=user)
        change_form = change_page.forms["objectsapigroupconfig_form"]
        change_form["catalogue_domain"] = "XXXXX"
        change_form["catalogue_rsin"] = "111222333"

        response = change_form.submit()

        assert response.status_code == 200
        self.assertContains(
            response,
            _(
                "The specified catalogue does not exist. Maybe you made a typo in the "
                "domain or RSIN?"
            ),
        )
