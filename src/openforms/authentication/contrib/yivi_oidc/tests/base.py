from pathlib import Path

from django.test import override_settings

from django_webtest import WebTest
from mozilla_django_oidc_db.tests.mixins import OIDCMixin

from openforms.utils.tests.vcr import OFVCRMixin

TEST_FILES = (Path(__file__).parent / "data").resolve()


@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class IntegrationTestsBase(OIDCMixin, OFVCRMixin, WebTest):
    VCR_TEST_FILES = TEST_FILES
