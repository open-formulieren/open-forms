from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.validators import AllOrNoneTruthyFieldsValidator
from openforms.utils.validators import RSINValidator


class CatalogueSerializer(serializers.Serializer):
    """
    Specify which catalogue to use to look up case/document types.

    Certain configuration models also define default fields like ``catalogue_domain``
    and ``catalogue_rsin`` to fall back on, such as:

    - :class:`openforms.registrations.contrib.objects_api.models.ObjectsAPIGroupConfig`
    - :class:`openforms.registrations.contrib.zgw_apis.models.ZGWApiGroupConfig`

    Use this serializer to persist the catalogue selection in registration backend
    options. When return available catalogues in an API endpoint, use
    :class:`openforms.contrib.zgw.api.serializers.CatalogueSerializer` instead.
    """

    domain = serializers.CharField(
        label=_("domain"),
        required=False,
        max_length=5,
        help_text=_(
            "The 'domein' attribute for the Catalogus resource in the Catalogi API."
        ),
        default="",
        allow_blank=True,
    )
    rsin = serializers.CharField(
        label=_("RSIN"),
        required=False,
        max_length=9,
        validators=[RSINValidator()],
        help_text=_(
            "The 'rsin' attribute for the Catalogus resource in the Catalogi API."
        ),
        default="",
        allow_blank=True,
    )

    class Meta:
        validators = [
            AllOrNoneTruthyFieldsValidator("domain", "rsin"),
        ]
