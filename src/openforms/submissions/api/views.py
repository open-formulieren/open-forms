from django.conf import settings
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import DestroyAPIView

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.serializers import ExceptionSerializer

from ..models import TemporaryFileUpload
from .permissions import OwnsTemporaryUploadPermission
from .renderers import FileRenderer


@extend_schema(
    summary=_("View/delete temporary upload."),
)
@extend_schema_view(
    get=extend_schema(
        summary=_("Retrieve temporary file upload"),
        description=_(
            "Retrieve temporary file upload for review by the uploader. \n\n"
            "This is called by the default Form.io file upload widget. \n\n"
            "Access to this view requires an active form submission. "
            "Unclaimed temporary files automatically expire after {expire_days} day(s). "
        ).format(expire_days=settings.TEMPORARY_UPLOADS_REMOVED_AFTER_DAYS),
        responses={
            (200, "application/octet-stream"): bytes,
        },
    ),
    delete=extend_schema(
        summary=_("Delete temporary file upload"),
        description=_(
            "Delete temporary file upload by the uploader. \n\n"
            "This is called by the default Form.io file upload widget. \n\n"
            "Access to this view requires an active form submission. "
            "Unclaimed temporary files automatically expire after {expire_days} day(s). "
        ),
        responses={
            204: None,
            ("4XX", CamelCaseJSONRenderer.media_type): ExceptionSerializer,
            ("5XX", CamelCaseJSONRenderer.media_type): ExceptionSerializer,
        },
    ),
)
class TemporaryFileView(DestroyAPIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = [OwnsTemporaryUploadPermission]
    renderer_classes = [FileRenderer, CamelCaseJSONRenderer]

    queryset = TemporaryFileUpload.objects.all()
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        upload = self.get_object()
        return sendfile(
            request,
            upload.content.path,
            attachment=True,
            attachment_filename=upload.file_name,
            mimetype=upload.content_type,
        )

    def perform_destroy(self, instance):
        # delete files from disc as well if they had been already
        # saved when trying to access the next form step
        instance.attachments.all().delete()
        instance.delete()
