from django.test import TestCase

from openforms.authentication.tests.factories import AttributeGroupFactory
from openforms.forms.tests.factories import FormAuthenticationBackendFactory


class AttributeGroupTest(TestCase):
    """
    Testing the AttributeGroup class.
    """

    def test_can_delete_group_when_not_used_by_any_form_authentication_backend(self):
        FormAuthenticationBackendFactory(backend="yivi_oidc", options={
            "additional_attributes_groups": [],
        })
        attribute_group = AttributeGroupFactory(name="group", description="description", attributes=[])
        attribute_group.delete()
        # expect attribute_group to be deleted

    def test_cannot_delete_group_when_used_in_form_authentication_backend(self):
        # @TODO
        # Define AttributeGroup
        # Define Yivi FormAuthenticationBackend that uses the AttributeGroup
        # Delete AttributeGroup and expect error
        pass

    def test_cannot_bulk_delete_group_when_used_in_form_authentication_backend(self):
        # @TODO
        # Define AttributeGroup
        # Define Yivi FormAuthenticationBackend that uses the AttributeGroup
        # Bulk delete AttributeGroup and expect error
        pass

    def test_when_changing_group_name_the_form_authentication_backend_that_used_it_will_also_update(self):
        # @TODO
        # Define AttributeGroup
        # Define Yivi FormAuthenticationBackend that uses the AttributeGroup
        # Update name of AttributeGroup
        # Expect that FormAuthenticationBackend AttributeGroup has also changed its name
        pass
