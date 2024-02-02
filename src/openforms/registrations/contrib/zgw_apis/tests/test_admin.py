from django.urls import reverse
from django.utils.translation import gettext as _

import requests
import requests_mock
from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.accounts.tests.factories import SuperUserFactory

from .factories import ZGWApiGroupConfigFactory


@disable_admin_mfa()
class ZGWApiGroupConfigAdminTests(WebTest):
    @requests_mock.Mocker()
    def test_admin_while_services_are_down(self, m):
        m.register_uri(
            requests_mock.ANY, requests_mock.ANY, exc=requests.ConnectTimeout
        )
        zgw_group = ZGWApiGroupConfigFactory.create(
            zrc_service__api_root="https://zaken-1.nl/api/v1/",
            zrc_service__oas="https://zaken-1.nl/api/v1/schema/openapi.yaml",
            drc_service__api_root="https://documenten-1.nl/api/v1/",
            drc_service__oas="https://documenten-1.nl/api/v1/schema/openapi.yaml",
            ztc_service__api_root="https://catalogus-1.nl/api/v1/",
            ztc_service__oas="https://catalogus-1.nl/api/v1/schema/openapi.yaml",
            zaaktype="https://catalogi-1.nl/api/v1/zaaktypen/1",
            informatieobjecttype="https://catalogi-1.nl/api/v1/informatieobjecttypen/1",
            organisatie_rsin="000000000",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        superuser = SuperUserFactory.create()

        response = self.app.get(
            reverse("admin:zgw_apis_zgwapigroupconfig_change", args=(zgw_group.pk,)),
            user=superuser,
        )

        self.assertEqual(response.status_code, 200)
        form = response.forms["zgwapigroupconfig_form"]
        self.assertEqual(
            form["zaaktype"].value, "https://catalogi-1.nl/api/v1/zaaktypen/1"
        )
        error_node = response.pyquery(
            ".field-zaaktype .openforms-error-widget .openforms-error-widget__column small"
        )
        self.assertEqual(
            error_node.text(),
            _(
                "Could not load data - enable and check the request "
                "logs for more details."
            ),
        )

        with self.subTest("submitting form doesn't clear configuration"):
            form.submit()

            zgw_group.refresh_from_db()
            self.assertEqual(
                zgw_group.zaaktype, "https://catalogi-1.nl/api/v1/zaaktypen/1"
            )
