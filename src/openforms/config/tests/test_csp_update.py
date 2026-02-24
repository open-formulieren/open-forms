from django.test import TestCase, override_settings

import csp.constants

from ..models import CSPSetting


def parse_csp_policy(header_value):
    # quick and dirty
    # "frame-ancestors 'self'; frame-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data: https://service.pdok.nl/ http://bazz.bar http://foo.bar; base-uri 'self'; default-src 'self'; report-uri /csp/report/"
    csp_values = dict()
    for line in header_value.split("; "):
        directive, v = line.split(" ", maxsplit=1)
        csp_values[directive] = v.split(" ")
    return csp_values


@override_settings(
    CONTENT_SECURITY_POLICY={
        "DIRECTIVES": {"default-src": [csp.constants.SELF]},
        "REPORT_URI": "/foo",
    },
    CONTENT_SECURITY_POLICY_REPORT_ONLY={},
)
class CSPUpdateTests(TestCase):
    def test_middleware_applies_cspsetting_models(self):
        CSPSetting.objects.create(directive="img-src", value="http://foo.bar")
        CSPSetting.objects.create(directive="img-src", value="http://bazz.bar")
        CSPSetting.objects.create(directive="default-src", value="http://buzz.bazz")

        response = self.client.get("/")
        self.assertIn("Content-Security-Policy", response.headers)
        csp_policy = parse_csp_policy(response.headers["Content-Security-Policy"])

        self.assertIn("http://foo.bar", csp_policy["img-src"])
        self.assertIn("http://bazz.bar", csp_policy["img-src"])
        self.assertIn("http://buzz.bazz", csp_policy["default-src"])
