from django.core.exceptions import ValidationError
from django.test import TestCase

from zgw_consumers.constants import APITypes
from zgw_consumers.test.factories import ServiceFactory

from ..models import ObjectsAPIGroupConfig


class ObjectsAPIConfigTests(TestCase):

    def test_invalid_objecttypes_url(self):
        config = ObjectsAPIGroupConfig(
            objecttypes_service=ServiceFactory.build(
                api_root="https://objecttypen.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            objecttype="https://example.com/api/dummy/",
        )

        self.assertRaises(ValidationError, config.clean)

    def test_valid_objecttypes_url(self):
        config = ObjectsAPIGroupConfig(
            objecttypes_service=ServiceFactory.build(
                api_root="https://objecttypen.nl/api/v1/",
                api_type=APITypes.orc,
            ),
            objecttype="https://objecttypen.nl/api/v1/objecttypes/1",
        )

        try:
            config.clean()
        except ValidationError as e:
            self.fail(f"Unexpected exception : {e}")
