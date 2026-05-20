from django.test import SimpleTestCase

from openforms.contrib.objects_api.models import ObjectsAPIGroupConfig
from openforms.contrib.objects_api.tests.factories import ObjectsAPIGroupConfigFactory

from ..utils import apply_defaults_to


class ObjectsAPIGroupTests(SimpleTestCase):
    def test_apply_defaults(self):
        api_group: ObjectsAPIGroupConfig = ObjectsAPIGroupConfigFactory.build()
        partial_opts = {}

        apply_defaults_to(api_group, partial_opts)

        self.assertEqual(
            partial_opts,
            {
                "organisatie_rsin": "",
                "version": 1,
            },
        )
