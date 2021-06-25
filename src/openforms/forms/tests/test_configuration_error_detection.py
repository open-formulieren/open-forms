import logging

from django.test import TestCase

from testfixtures import log_capture

from ..tasks import detect_formiojs_configuration_snake_case
from .factories import FormDefinitionFactory


class SnakeCaseDetectionTests(TestCase):
    @log_capture(level=logging.ERROR)
    def test_all_camelcase(self, capture):
        configuration = {"lowercase": {"camelCase": {}}}
        fd = FormDefinitionFactory.create(configuration=configuration)

        detect_formiojs_configuration_snake_case(fd.id)

        capture.check()

    @log_capture(level=logging.ERROR)
    def test_all_lowercase(self, capture):
        configuration = {"lowercase": {"lower": {}}}
        fd = FormDefinitionFactory.create(configuration=configuration)

        detect_formiojs_configuration_snake_case(fd.id)

        capture.check()

    @log_capture(level=logging.ERROR)
    def test_snake_case(self, capture):
        configuration = {"lowercase": {"snake_case": {}}}
        fd = FormDefinitionFactory.create(configuration=configuration)

        detect_formiojs_configuration_snake_case(fd.id)

        msg = (
            f"FormDefinition with ID {fd.id} appears to contain snake_case keys in "
            "its formiojs configuration. This is known to cause issues with the "
            "prefill module."
        )
        capture.check(
            ("openforms.forms.tasks", "ERROR", msg),
        )
