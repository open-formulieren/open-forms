from django.db import transaction
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.authentication import AnonCSRFSessionAuthentication
from openforms.api.views import ListMixin
from openforms.submissions.api.permissions import ActiveSubmissionPermission
from openforms.submissions.models import Submission

from ..registry import register
from ..utils import logout_submission
from .serializers import AuthPluginSerializer


@extend_schema_view(
    get=extend_schema(summary=_("List available authentication plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all authentication plugins that have been registered.

    Each authentication plugin is tied to a particular (third-party) authentication
    provider. An authentication plugin usually provides a particular authentication
    attribute, such as the ``BSN`` or Chamber of Commerce number. A plugin may provide
    zero, one or multiple authentication attributes.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = AuthPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())


class SubmissionLogoutView(GenericAPIView[Submission]):
    authentication_classes = (AnonCSRFSessionAuthentication,)
    permission_classes = (ActiveSubmissionPermission,)
    serializer_class = (
        serializers.Serializer
    )  # just to shut up some warnings in drf-spectacular

    queryset = Submission.objects.all()
    lookup_field = "uuid"

    @extend_schema(
        operation_id="submission_session_destroy",
        summary=_("Delete form session"),
        description=_(
            "Calling this endpoint will clear the current form and submission from the session. "
            "This also clears the form authentication state and calls the authentication plugin logout handler, if authenticated. "
        ),
    )
    @transaction.atomic()
    def delete(self, request, *args, **kwargs):
        submission = self.get_object()

        logout_submission(submission, request)

        if submission.is_ready_to_hash_identifying_attributes:
            if not submission.auth_info.attribute_hashed:
                submission.auth_info.hash_identifying_attributes()

            if (
                registrator := submission.registrator
            ) and not registrator.attribute_hashed:
                registrator.hash_identifying_attributes()

        return Response(status=status.HTTP_204_NO_CONTENT)
