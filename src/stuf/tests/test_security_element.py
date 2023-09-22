from django.template.loader import render_to_string
from django.test import SimpleTestCase

from freezegun import freeze_time
from lxml import etree

from soap.constants import EndpointSecurity

from ..client import BaseClient
from ..service_client_factory import ServiceClientFactory, get_client_init_kwargs
from .factories import StufServiceFactory


class SecurityElementTests(SimpleTestCase):
    @freeze_time("2023-02-03T15:09:27+01:00")
    def test_resolution_timestamps(self):
        nsmap = {
            "soap": "http://www.w3.org/2003/05/soap-envelope",
            "wss": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
        }
        service = StufServiceFactory.build(
            soap_service__user="some-username",
            soap_service__password="some-password",
            soap_service__endpoint_security=EndpointSecurity.wss,
        )
        factory = ServiceClientFactory(service)
        client = BaseClient.configure_from(factory, **get_client_init_kwargs(service))
        client.soap_security_expires_minutes = 5
        context = client.build_base_context()

        output = render_to_string("stuf/soap_envelope.xml", context=context).encode(
            "utf-8"
        )

        xml_doc = etree.fromstring(output)
        security = xml_doc.xpath("soap:Header/wss:Security", namespaces=nsmap)[0]
        username_token = security.xpath("./wss:UsernameToken", namespaces=nsmap)
        self.assertTrue(username_token)
        timestamp = security.xpath("./wss:Timestamp", namespaces=nsmap)[0]

        created = timestamp.xpath("./wss:Created", namespaces=nsmap)[0].text
        self.assertEqual(created, "2023-02-03T14:09:27Z")
        expires = timestamp.xpath("./wss:Expires", namespaces=nsmap)[0].text
        self.assertEqual(expires, "2023-02-03T14:14:27Z")
