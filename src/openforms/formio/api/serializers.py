from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.reverse import reverse

from openforms.submissions.constants import SUBMISSIONS_SESSION_KEY
from openforms.submissions.models import Submission

from .validators import MimeTypeValidator, NoVirusValidator


class TemporaryFileUploadSerializer(serializers.Serializer):
    """
    https://help.form.io/integrations/filestorage/#url

    {
        url: 'http://link.to/file',
        name: 'The_Name_Of_The_File.doc',
        size: 1000
    }
    """

    file = serializers.FileField(
        write_only=True,
        required=True,
        use_url=False,
        validators=[MimeTypeValidator(), NoVirusValidator()],
    )
    submission = serializers.HyperlinkedRelatedField(
        view_name="api:submission-detail",
        lookup_field="uuid",
        queryset=Submission.objects.all(),
        label=_("Submission"),
        write_only=True,
        required=True,
    )

    url = serializers.SerializerMethodField(
        label=_("URL"), source="get_url", read_only=True
    )
    name = serializers.CharField(
        label=_("File name"), source="file_name", read_only=True
    )
    size = serializers.IntegerField(
        label=_("File size"), source="content.size", read_only=True
    )

    def get_url(self, instance) -> str:
        request = self.context["request"]
        return reverse(
            "api:submissions:temporary-file",
            kwargs={"uuid": instance.uuid},
            request=request,
        )

    def validate_submission(self, submission: Submission) -> Submission:
        if submission.uuid not in self.context["request"].session.get(
            SUBMISSIONS_SESSION_KEY, []
        ):
            raise serializers.ValidationError({"submission": _("Invalid submission")})

        return submission
