from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.api.validators import AllOrNoneTruthyFieldsValidator
from openforms.utils.validators import RSINValidator


class CatalogueSerializer(serializers.Serializer):
    """
    Specify which catalogue to use to look up case/document types.

    Note that domain/rsin both need to be not-empty to correctly identify a catalogue
    in the Catalogi API, but we allow blank values so that the parent serializer can
    make the ``catalogue`` field required with empty options if the catalogue is not
    a hard requirement, which simplifies runtime code.

    Use this serializer to persist the catalogue selection in registration backend
    options. When returning available catalogues in an API endpoint, use
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
