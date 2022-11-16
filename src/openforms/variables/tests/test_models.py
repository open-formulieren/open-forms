from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

import factory
from model_bakery import baker

from ..models import DataMappingTypes, ServiceFetchConfiguration, ServiceFetchMethods


class ServiceFetchConfigurationFactory(factory.django.DjangoModelFactory):
    """An incomplete ServiceFetchConfiguration factory

    no service is created.
    """

    class Meta:
        model = ServiceFetchConfiguration

    service = None  # No
    path = ""
    method = "GET"
    headers = None
    query_params = ""
    body = None
    data_mapping_type = None
    mapping_expression = None


class ServiceFetchConfigurationTests(SimpleTestCase):
    def test_body_on_get_request_should_be_empty(self):
        null = ServiceFetchConfiguration(
            method="GET",
            body=None,
        )
        empty = ServiceFetchConfiguration(
            method="GET",
            body="",
        )
        not_empty = ServiceFetchConfiguration(
            method="GET",
            body="{}",
        )

        null.clean_fields(exclude="service")
        empty.clean_fields(exclude="service")
        with self.assertRaisesMessage(ValidationError, "GET request"):
            not_empty.clean_fields(exclude="service")

    def test_mapping_expresssion_should_be_empty_if_no_type_is_known(self):
        null = ServiceFetchConfiguration(
            data_mapping_type=None,
            mapping_expression=None,
        )
        empty = ServiceFetchConfiguration(
            data_mapping_type=None,
            mapping_expression="",
        )
        valid_jq = ServiceFetchConfiguration(
            data_mapping_type=None,
            mapping_expression=".",  # identity
        )

        null.clean_fields(exclude="service")
        empty.clean_fields(exclude="service")
        with self.assertRaisesMessage(ValidationError, "expression"):
            valid_jq.clean_fields(exclude="service")

    def test_jq_mapping_expression_validation(self):
        valid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.jq,
            mapping_expression=".",  # identity
        )
        invalid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.jq,
            mapping_expression="asdf",
        )

        valid_expression.clean_fields(exclude="service")
        with self.assertRaisesMessage(ValidationError, "asdf"):
            invalid_expression.clean_fields(exclude="service")

    def test_json_logic_mapping_expression_validation(self):
        valid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.json_logic,
            mapping_expression={"var": 0},  # first member
        )
        invalid_expression = ServiceFetchConfiguration(
            data_mapping_type=DataMappingTypes.json_logic,
            mapping_expression={"fdsa": 0},
        )

        valid_expression.clean_fields(exclude="service")
        with self.assertRaisesMessage(ValidationError, "fdsa"):
            invalid_expression.clean_fields(exclude="service")
