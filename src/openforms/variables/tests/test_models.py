from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ..constants import DataMappingTypes, ServiceFetchMethods
from ..models import ServiceFetchConfiguration


class ServiceFetchConfigurationTests(SimpleTestCase):
    def test_body_on_get_request_should_be_empty(self):
        null = ServiceFetchConfiguration(
            method=ServiceFetchMethods.get,
            body=None,
        )
        empty = ServiceFetchConfiguration(
            method=ServiceFetchMethods.get,
            body="",
        )
        not_empty = ServiceFetchConfiguration(
            method=ServiceFetchMethods.get,
            body="{}",
        )

        null.clean()
        empty.clean()
        with self.assertRaisesMessage(ValidationError, "GET request"):
            not_empty.clean()

    def test_mapping_expresssion_should_be_empty_if_no_type_is_known(self):
        null = ServiceFetchConfiguration(
            data_mapping_type="",
            mapping_expression=None,
        )
        empty = ServiceFetchConfiguration(
            data_mapping_type="",
            mapping_expression="",
        )
        valid_jq = ServiceFetchConfiguration(
            data_mapping_type="",
            mapping_expression=".",  # identity
        )

        null.clean()
        empty.clean()
        with self.assertRaises(ValidationError) as exc_wrapper:
            valid_jq.clean()

        exception = exc_wrapper.exception
        self.assertIn("data_mapping_type", exception.message_dict)

    def test_empty_expressions_should_not_break(self):
        # Empty JSONFields are coerced to None
        for mapping_type in DataMappingTypes.values:
            expression = ServiceFetchConfiguration(
                data_mapping_type=mapping_type,
                mapping_expression=None,
            )
            with self.subTest(mapping_type):
                try:
                    expression.clean()
                except ValidationError:
                    pass
                except Exception as e:
                    raise self.failureException("Unexpected exception type") from e

    def test_jq_mapping_expression_validation(self):
        valid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.jq,
            mapping_expression=".",  # identity
        )
        invalid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.jq,
            mapping_expression="asdf",
        )

        valid_expression.clean()
        with self.assertRaisesMessage(ValidationError, "asdf"):
            invalid_expression.clean()

    def test_json_logic_mapping_expression_validation(self):
        valid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.json_logic,
            mapping_expression={"var": 0},  # first member
        )
        invalid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.json_logic,
            mapping_expression={"fdsa": 0},
        )

        valid_expression.clean()
        with self.assertRaisesMessage(ValidationError, "fdsa"):
            invalid_expression.clean()

    def test_http_request_headers(self):
        valid_headers = ServiceFetchConfiguration(
            name="foo", headers={"X-Custom-Header": "foo bar 30.0"}
        )
        invalid_headers = ServiceFetchConfiguration(
            name="bar",
            headers={
                "X-invalid-field-content": 30.0,
            },
        )

        valid_headers.full_clean(exclude={"service"})

        with self.assertRaisesMessage(ValidationError, "X-invalid-field-content"):
            invalid_headers.full_clean(exclude={"service"})
