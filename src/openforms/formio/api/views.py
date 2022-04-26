import os

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from openforms.api.parsers import MaxFilesizeMultiPartParser
from openforms.submissions.api.permissions import AnyActiveSubmissionPermission
from openforms.submissions.api.renderers import PlainTextErrorRenderer
from openforms.submissions.api.serializers import TemporaryFileUploadSerializer
from openforms.submissions.attachments import clean_mime_type
from openforms.submissions.models import TemporaryFileUpload
from openforms.submissions.utils import add_upload_to_session


@extend_schema(
    summary=_("Create temporary file upload"),
    description=_(
        'File upload handler for the Form.io file upload "url" storage type.\n\n'
        "The uploads are stored temporarily and have to be claimed by the form submission "
        "using the returned JSON data. \n\n"
        "Access to this view requires an active form submission. "
        "Unclaimed temporary files automatically expire after {expire_days} day(s). \n\n"
        "The maximum upload size for this instance is `{max_upload_size}`. Note that "
        "this includes the multipart metadata and boundaries, so the actual maximum "
        "file upload size is slightly smaller."
    ).format(
        expire_days=settings.TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS,
        max_upload_size=filesizeformat(settings.MAX_FILE_UPLOAD_SIZE),
    ),
)
class TemporaryFileUploadView(GenericAPIView):
    parser_classes = [MaxFilesizeMultiPartParser]
    serializer_class = TemporaryFileUploadSerializer
    authentication_classes = []
    permission_classes = [AnyActiveSubmissionPermission]
    renderer_classes = [CamelCaseJSONRenderer]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
                content_type="text/plain",
            )

        file = serializer.validated_data["file"]

        # trim name part if necessary but keep the extension
        name, ext = os.path.splitext(file.name)
        name = name[: 255 - len(ext)] + ext

        upload = TemporaryFileUpload.objects.create(
            content=file,
            file_name=name,
            content_type=clean_mime_type(file.content_type),
            file_size=file.size,
        )
        add_upload_to_session(upload, self.request.session)

        return Response(
            self.serializer_class(instance=upload, context={"request": request}).data
        )

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Override renderer to support JSON for success and text for error response
        """
        if response.status_code == 400:
            request.accepted_renderer = PlainTextErrorRenderer()
            request.accepted_media_type = "text/plain"
        response = super().finalize_response(request, response, *args, **kwargs)
        return response
