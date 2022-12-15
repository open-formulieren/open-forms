from pathlib import Path

from django.test import TestCase

import requests_mock
from factory.django import FileField
from zgw_consumers.constants import APITypes

from openforms.forms.tests.factories import FormVariableFactory
from openforms.variables.constants import DataMappingTypes
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ...form_logic import bind


class ServiceFetchConfigVariableBindingTests(TestCase):
    @requests_mock.Mocker()
    def test_it_performs_simple_get(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})
        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service__api_type=APITypes.orc,
                service__api_root="https://httpbin.org/",
                service__oas_file=FileField(
                    from_path=str(
                        Path(__file__).parent.parent / "files" / "openapi.yaml"
                    )
                ),
                path="get",
            )
        )

        value = bind(var, {})

        self.assertEqual(value["url"], "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_applies_jsonlogic(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service__api_type=APITypes.orc,
                service__api_root="https://httpbin.org/",
                service__oas_file=FileField(
                    from_path=str(
                        Path(__file__).parent.parent / "files" / "openapi.yaml"
                    )
                ),
                path="get",
                data_mapping_type=DataMappingTypes.json_logic,
                mapping_expression={"var": "url"},
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_applies_jq(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service__api_type=APITypes.orc,
                service__api_root="https://httpbin.org/",
                service__oas_file=FileField(
                    from_path=str(
                        Path(__file__).parent.parent / "files" / "openapi.yaml"
                    )
                ),
                path="get",
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression=".url",
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_applies_request_headers(self, m):
        m.get("https://httpbin.org/get")

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service__api_type=APITypes.orc,
                service__api_root="https://httpbin.org/",
                service__oas_file=FileField(
                    from_path=str(
                        Path(__file__).parent.parent / "files" / "openapi.yaml"
                    )
                ),
                path="get",
                headers={"X-Brony-Identity": "Jumper"},
            )
        )

        _ = bind(var, {})
        request_headers = m.last_request.headers

        self.assertIn(("X-Brony-Identity", "Jumper"), request_headers.items())

    @requests_mock.Mocker()
    def test_it_sends_the_body_as_json(self, m):
        m.get("https://httpbin.org/anything", json="Armour")

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service__api_type=APITypes.orc,
                service__api_root="https://httpbin.org/",
                service__oas_file=FileField(
                    from_path=str(
                        Path(__file__).parent.parent / "files" / "openapi.yaml"
                    )
                ),
                path="anything",
                body="Armour",
            )
        )

        _ = bind(var, {})
        request = m.last_request

        self.assertIn(("Content-Type", "application/json"), request.headers.items())
        self.assertEqual(request.body, b'"Armour"')

    def test_it_does_not_swallow_unknown_types(self):
        var = FormVariableFactory.create()

        with self.assertRaises(NotImplementedError):
            bind(var, {})
