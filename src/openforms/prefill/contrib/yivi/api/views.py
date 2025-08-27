from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, views

from openforms.api.views import ListMixin
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup

from .serializers import YiviPrefillAttributeApiResponse, YiviPrefillAttributeSerializer


@extend_schema_view(
    get=extend_schema(summary=_("List available Yivi prefill attributes")),
)
class AttributeGroupListView(ListMixin, views.APIView):
    """
    List all Yivi prefill attributes, based on the Yivi attribute groups.

    This endpoint lists all available Yivi attribute groups, and is used for Yivi
    authentication and prefill plugin configuration. The `prefill_attributes` and
    `is_virtual` are solely used for the Yivi prefill plugin configuration.

    `prefill_attributes` contains the attributes that are derived from the
    attribute group.

    `is_virtual` is used for attribute groups that don't actually exist. These attribute
    groups are added to pass any additional Yivi prefill attributes to the frontend
    (like the prefill attributes for identifier and loa values).
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = YiviPrefillAttributeSerializer

    def _get_virtual_prefill_attribute_groups(
        self,
    ) -> list[YiviPrefillAttributeApiResponse]:
        virtual_prefill_attribute_group: YiviPrefillAttributeApiResponse = {
            "attribute_group_uuid": "00000000-0000-0000-0000-000000000000",
            "attributes": [
                {
                    "label": _("Identifier"),
                    "value": "value",
                },
                {
                    "label": _("Level of Assurance"),
                    "value": "loa",
                },
            ],
            "is_static": True,
        }

        return [virtual_prefill_attribute_group]

    def get_objects(self) -> list[YiviPrefillAttributeApiResponse]:
        prefill_attribute_groups: list[YiviPrefillAttributeApiResponse] = []

        for group in AttributeGroup.objects.all():
            prefill_attribute: YiviPrefillAttributeApiResponse = {
                "attribute_group_uuid": group.uuid,
                "attributes": [
                    {
                        "label": attribute,
                        # In the backend, the periods in Yivi attributes have been replaced
                        # with underscores. Make sure these attributes are also updated.
                        # https://github.com/open-formulieren/open-forms/issues/5475
                        "value": f"additional_claims.{attribute.replace('.', '_')}",
                    }
                    for attribute in group.attributes
                ],
                "is_static": False,
            }
            prefill_attribute_groups.append(prefill_attribute)

        return prefill_attribute_groups + self._get_virtual_prefill_attribute_groups()
