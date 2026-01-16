from typing import Any
from unittest import skip
from urllib.parse import unquote

from django.core.exceptions import SuspiciousOperation
from django.test import SimpleTestCase, tag

import requests_mock
from furl import furl
from hypothesis import assume, example, given, strategies as st
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.test.factories import ServiceFactory

from openforms.formio.service import FormioData
from openforms.forms.tests.factories import FormVariableFactory
from openforms.utils.tests.nlx import DisableNLXRewritingMixin
from openforms.variables.constants import DataMappingTypes
from openforms.variables.models import _convert_to_string
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory
from openforms.variables.validators import HeaderValidator, ValidationError

from ...logic.service_fetching import perform_service_fetch

DEFAULT_REQUEST_HEADERS = {
    "Accept",
    "Accept-Encoding",
    "Connection",
    "User-Agent",
}


def data_mapping_values() -> st.SearchStrategy[Any]:
    "Generates values for the value side of openforms.typing.DataMapping"
    return st.one_of(st.text(), st.integers(), st.floats(), st.dates(), st.datetimes())


class ServiceFetchConfigVariableBindingTests(DisableNLXRewritingMixin, SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = ServiceFactory.build(
            api_type=APITypes.orc,
            api_root="https://httpbin.org/",
            auth_type=AuthTypes.no_auth,
        )

    @requests_mock.Mocker()
    def test_it_performs_simple_get(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
            )
        )

        result = perform_service_fetch(var, FormioData())
        value = result.value

        self.assertEqual(value["url"], "https://httpbin.org/get")

    def test_it_can_construct_service_endpoint_path_parameters_from_a_well_behaved_user(
        self,
    ):
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="delay/{{seconds}}",
            )
        )
        context = FormioData({"seconds": 6})

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, json={})
            perform_service_fetch(var, context)
            request = m.last_request

        self.assertEqual(request.url, "https://httpbin.org/delay/6")

    def test_substitutions_all_happen_at_once(self):
        # It should not be possible for substitution values to be interpreted as template variables
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="delay/{{seconds}}.{{second_fragments}}",
            )
        )
        # Intended use
        context = FormioData({"seconds": 6, "second_fragments": "5"})

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, json={})
            perform_service_fetch(var, context)
            request = m.last_request

        self.assertEqual(request.url, "https://httpbin.org/delay/6.5")

        # Edge case
        context = FormioData({"seconds": 6, "second_fragments": "{{seconds}}"})

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, json={})
            perform_service_fetch(var, context)
            request = m.last_request

        self.assertEqual(request.url, "https://httpbin.org/delay/6.%7B%7Bseconds%7D%7D")

    @given(data_mapping_values())
    @example("../otherendpoint")
    @example("./../.")
    @example("foo/ +.")
    def test_it_can_construct_simple_path_parameters_from_any_input(self, field_value):
        # request_mock eats the single dot :pacman:, and ".." is disallowed:
        assume(field_value not in {".", ".."})
        # https://swagger.io/docs/specification/describing-parameters/#path-parameters
        context = FormioData({"late": {"seconds": field_value}})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="delay/{{late.seconds}}",  # this is not defined as number in the OAS
            )
        )

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY, json={})
            _ = perform_service_fetch(var, context)
            request = m.last_request

        expected_stem_length = len("https://httpbin.org/delay/")
        stem = request.url[:expected_stem_length]
        rest = request.url[expected_stem_length:]

        self.assertEqual(stem, "https://httpbin.org/delay/")
        # values should not be able to traverse the api tree
        self.assertNotIn("/", rest)
        self.assertNotIn(" ", rest)
        # the service should get the value
        self.assertEqual(unquote(rest), str(field_value))

        # I guess if `rest` is unmangled, the following assertions are
        # tautologies; Better safe than sorry. They MUST hold, even if I can't
        # think of a way they can't be true.

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertIs(request.query, "")
        self.assertEqual(set(request.headers), DEFAULT_REQUEST_HEADERS)
        # and a weak assertion
        self.assertNotIn(str(field_value), request.headers.values())

    @tag("gh-4015")
    def test_raises_suspicious_operation_on_double_dot_input(self):
        context = FormioData({"late": {"seconds": ".."}})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="delay/{{late.seconds}}",  # this is not defined as number in the OAS
            )
        )

        with self.assertRaises(SuspiciousOperation):
            perform_service_fetch(var, context)

    # TODO
    @tag("gh-2745")
    @given(
        st.one_of(
            st.lists(elements=data_mapping_values()),
            st.dictionaries(
                keys=st.text(), values=st.one_of(st.text(), st.integers(), st.floats())
            ),
        )
    )
    def test_it_can_construct_product_type_path_parameters(self, field_value):
        # serialize lists and dicts of values as specified by `style` and
        # `explode` in the oas-spec of the service
        # https://swagger.io/docs/specification/serialization/
        ...

    @given(field_value=data_mapping_values())
    def test_it_can_construct_simple_query_parameters(self, field_value):
        # https://swagger.io/docs/specification/describing-parameters/#query-parameters
        context = FormioData({"some_field": field_value})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="response-headers",
                query_params={"freeform": "{{some_field}}"},
            )
        )

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get(
                furl("https://httpbin.org/response-headers")
                .set({"freeform": _convert_to_string(field_value)})
                .url,
                json={},
            )
            _ = perform_service_fetch(var, context)
            request = m.last_request

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertEqual(set(request.headers), DEFAULT_REQUEST_HEADERS)
        # and a weak assertion
        self.assertNotIn(str(field_value), request.headers.values())

    @given(
        st.text(),  # OAS schema: type: string
        data_mapping_values(),
    )
    def test_it_can_construct_multiple_simple_query_parameters(
        self, some_text, some_value
    ):
        # https://swagger.io/docs/specification/describing-parameters/#query-parameters
        context = FormioData({"url": some_text, "code": [{"foo": some_value}]})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="redirect-to",
                query_params={"status_code": ["{{code.0.foo}}"], "url": ["{{url}}"]},
            )
        )

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get(
                furl("https://httpbin.org/redirect-to")
                .set({"url": some_text, "status_code": _convert_to_string(some_value)})
                .url,
                json={},
            )
            _ = perform_service_fetch(var, context)
            request = m.last_request

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertEqual(set(request.headers), DEFAULT_REQUEST_HEADERS)
        # and some weak assertions
        self.assertNotIn(str(some_text), request.headers.values())
        self.assertNotIn(str(some_value), request.headers.values())

    # TODO
    @tag("gh-2745")
    @given(
        st.one_of(
            st.lists(elements=st.one_of(st.text(), st.integers(), st.floats())),
            st.dictionaries(
                keys=st.text(), values=st.one_of(st.text(), st.integers(), st.floats())
            ),
        )
    )
    def test_it_can_construct_product_type_query_parameters(self, field_value):
        # serialize lists and dicts of values as specified by `style` and
        # `explode` in the oas-spec of the service
        # https://swagger.io/docs/specification/serialization/
        ...

    @requests_mock.Mocker()
    def test_it_sends_request_headers(self, m):
        m.get("https://httpbin.org/get", json={})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                headers={"X-Brony-Identity": "Jumper"},
            )
        )

        _ = perform_service_fetch(var, FormioData())
        request_headers = m.last_request.headers

        self.assertIn(("X-Brony-Identity", "Jumper"), request_headers.items())

    def test_it_can_construct_simple_header_parameters(self):
        """Assert a happy path"""
        # https://swagger.io/docs/specification/describing-parameters/#header-parameters
        context = FormioData({"some": [{"nested_value": "x"}]})
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="cache",
                # our OAS spec doesn't care what ETags look like.
                headers={"If-None-Match": "{{some.0.nested_value}}"},
            )
        )
        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get("https://httpbin.org/cache", json={})
            _ = perform_service_fetch(var, context)
            request = m.last_request

        self.assertIn(("If-None-Match", "x"), request.headers.items())

    @given(data_mapping_values())
    @example("Little Bobby Tables\r\nX-Other-Header: Some value")
    def test_it_never_sends_bad_headers_regardless_of_what_people_submit(
        self, field_value
    ):
        context = FormioData({"some_value": field_value})
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="cache",
                headers={"If-None-Match": "{{some_value}}"},
            )
        )

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get("https://httpbin.org/cache", json={})
            try:
                # when we bind
                _ = perform_service_fetch(var, context)
            except Exception:  # XXX unclear what exception to expect
                # either raise an exception
                return

        # or place a welformed request
        request = m.last_request
        try:
            HeaderValidator()(request.headers)
        except ValidationError as e:
            raise self.failureException("Fetch sent bad headers!") from e

        # it should not add any other headers
        self.assertEqual(
            set(request.headers), {"If-None-Match"}.union(DEFAULT_REQUEST_HEADERS)
        )

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertEqual(request.path, "/cache")
        self.assertEqual(len(request.qs), 0)

    @requests_mock.Mocker()
    def test_it_sends_the_body_as_json(self, m):
        m.get("https://httpbin.org/anything", json="Armour")

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="anything",
                body="Armour",
            )
        )

        _ = perform_service_fetch(var, FormioData())
        request = m.last_request

        self.assertIn(("Content-Type", "application/json"), request.headers.items())
        self.assertEqual(request.body, b'"Armour"')

    @requests_mock.Mocker()
    def test_it_applies_jsonlogic_on_response(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.json_logic,
                mapping_expression={"var": "url"},
            )
        )

        result = perform_service_fetch(var, FormioData())
        value = result.value

        self.assertEqual(value, "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_applies_jq_on_response(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression=".url",
            )
        )

        result = perform_service_fetch(var, FormioData())
        value = result.value

        self.assertEqual(value, "https://httpbin.org/get")

    @skip("This will go into an infinite loop")
    @tag("dangerous", "gh-2744")
    @requests_mock.Mocker()
    def test_it_does_not_hang_on_infinite_jq_recursion(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression="[while(.;.)]",
            )
        )

        result = perform_service_fetch(var, FormioData())
        value = result.value

        self.assertEqual(value, "https://httpbin.org/get")

    def test_it_raises_value_errors(self):
        var = FormVariableFactory.build()

        with self.assertRaises(ValueError):
            perform_service_fetch(var, FormioData())
