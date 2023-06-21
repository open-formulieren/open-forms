from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.template.validators import DjangoTemplateValidator
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.validators import validate_rsin


class ObjectsAPIOptionsSerializer(JsonSchemaSerializerMixin, serializers.Serializer):
    objecttype = serializers.URLField(
        label=_("objecttype"),
        help_text=_(
            "URL that points to the ProductAanvraag objecttype in the Objecttypes API. "
            "The objecttype should have the following three attributes: "
            "1) submission_id; "
            "2) type (the type of productaanvraag); "
            "3) data (the submitted form data)"
        ),
        required=False,
    )
    objecttype_version = serializers.IntegerField(
        label=_("objecttype version"),
        help_text=_("Version of the objecttype in the Objecttypes API"),
        required=False,
    )
    productaanvraag_type = serializers.CharField(
        label=_("productaanvraag type"),
        help_text=_("The type of ProductAanvraag"),
        required=False,
    )
    informatieobjecttype_submission_report = serializers.URLField(
        label=_("submission report PDF informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report PDF"
        ),
        required=False,
    )
    upload_submission_csv = serializers.BooleanField(
        label=_("Upload submission CSV"),
        help_text=_(
            "Indicates whether or not the submission CSV should be uploaded as "
            "a Document in Documenten API and attached to the ProductAanvraag"
        ),
        default=False,
    )
    informatieobjecttype_submission_csv = serializers.URLField(
        label=_("submission report CSV informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission report CSV"
        ),
        required=False,
    )
    informatieobjecttype_attachment = serializers.URLField(
        label=_("attachment informatieobjecttype"),
        help_text=_(
            "URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API "
            "to be used for the submission attachments"
        ),
        required=False,
    )
    organisatie_rsin = serializers.CharField(
        label=_("organisation RSIN"),
        required=False,
        validators=[validate_rsin],
        help_text=_("RSIN of organization, which creates the INFORMATIEOBJECT"),
    )
    content_json = serializers.CharField(
        label=_("JSON content field"),
        help_text=_(
            "JSON template for the body of the request sent to the Objects API."
        ),
        validators=[
            DjangoTemplateValidator(
                backend="openforms.template.openforms_backend",
            ),
        ],
        required=False,
    )
