from pathlib import Path
from unittest import skip
from urllib.parse import unquote

import requests_mock
from factory.django import FileField
from hypothesis import example, given, strategies as st
from hypothesis.extra.django import TestCase
from zgw_consumers.constants import APITypes

from openforms.forms.tests.factories import FormVariableFactory
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.variables.constants import DataMappingTypes
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ...form_logic import bind


class ServiceFetchConfigVariableBindingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = ServiceFactory(
            api_type=APITypes.orc,
            api_root="https://httpbin.org/",
            oas_file=FileField(
                from_path=str(Path(__file__).parent.parent / "files" / "openapi.yaml")
            ),
        )

    @requests_mock.Mocker()
    def test_it_performs_simple_get(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})
        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service=self.service,
                path="get",
            )
        )

        value = bind(var, {})

        self.assertEqual(value["url"], "https://httpbin.org/get")

    @given(
        st.one_of(st.text(), st.integers(), st.floats())
    )  # XXX is this complete? st.datetimes?
    @example("../otherendpoint")
    def test_it_takes_simple_path_parameters(self, field_value):
        # https://swagger.io/docs/specification/describing-parameters/#path-parameters

        self.service.oas_file.seek(0)  # oas fetcher reads n times
        context = {"seconds": field_value}

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service=self.service,
                path="delay/{seconds}",
            )
        )

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY)
            _ = bind(var, context)
            request = m.last_request

        head, rest = request.url[:26], request.url[26:]
        self.assertEqual(head, "https://httpbin.org/delay/")
        # the service should get the value
        self.assertEqual(unquote(rest), str(field_value))

        # I guess if the rest is unmangled, the rest of the assertions are not
        # really needed; I think
        # ∄ a way for Bobby Tables to drop a table ∧ become an unmangled entry in it
        # but asserting is cheaper than a CVE

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertIs(request.query, "")
        # it shouldn't mess with authentication headers
        for header, value in self.service.build_client().auth.credentials().items():
            self.assertEqual(request.headers[header], value)
        # and some weak assertions
        self.assertNotIn(str(field_value), request.headers)
        self.assertNotIn(str(field_value), request.headers.values())

    @skip("TODO: Implement")
    @given(
        st.one_of(
            st.lists(elements=st.one_of(st.text(), st.integers(), st.floats())),
            st.dictionaries(
                keys=st.text(), values=st.one_of(st.text(), st.integers(), st.floats())
            ),
        )
    )
    def test_it_takes_product_type_path_parameters(self, field_value):
        # serialize lists and dicts of values as specified by `style` and
        # `explode` in the oas-spec of the service
        # https://swagger.io/docs/specification/serialization/
        ...

    @requests_mock.Mocker()
    def test_it_applies_jsonlogic_on_response(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.json_logic,
                mapping_expression={"var": "url"},
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_applies_jq_on_response(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression=".url",
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_sends_request_headers(self, m):
        m.get("https://httpbin.org/get")

        var = FormVariableFactory.create(
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(
                service=self.service,
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
                service=self.service,
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
