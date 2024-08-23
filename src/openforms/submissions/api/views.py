from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django_sendfile import sendfile
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.serializers import ExceptionSerializer
from openforms.submissions.models.email_verification import EmailVerification

from ..models import TemporaryFileUpload
from .permissions import AnyActiveSubmissionPermission, OwnsTemporaryUploadPermission
from .renderers import FileRenderer
from .serializers import EmailVerificationSerializer, VerifyEmailSerializer


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


@extend_schema(
    summary=_("Start email verification"),
    description=_(
        "Create an email verification resource to start the verification process. "
        "A verification e-mail will be scheduled and sent to the provided email "
        "address, containing the verification code to use during verification.\n\n"
        "Validations check that the provided component key is present in the form of "
        "the submission and that it actually is an `email` component."
    ),
)
class EmailVerificationCreateView(CreateAPIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = (AnyActiveSubmissionPermission,)
    serializer_class = EmailVerificationSerializer
    # using none to prevent potential accidents - the view only needs to know about
    # queryset.model anyway
    queryset = EmailVerification.objects.none()

    def perform_create(self, serializer):
        super().perform_create(serializer)
        verification = serializer.instance
        assert isinstance(verification, EmailVerification)
        transaction.on_commit(verification.send_email)


@extend_schema(
    summary=_("Verify email address"),
    description=_(
        "Using the code obtained from the verification email, mark the email address "
        "as verified. Using an invalid code results in validation errors in the error "
        "response."
    ),
)
class VerifyEmailView(APIView):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = (AnyActiveSubmissionPermission,)

    def get_serializer_class(self):
        return VerifyEmailSerializer

    def get_serializer_context(self):
        return {"request": self.request, "view": self}

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        verification = serializer.instance
        assert isinstance(verification, EmailVerification)
        verification.verified_on = timezone.now()
        verification.save()
        return Response(serializer.data)
