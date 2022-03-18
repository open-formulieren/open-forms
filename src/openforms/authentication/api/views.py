from django.db import transaction
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions, serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.submissions.utils import (
    get_submissions_from_session,
    remove_submission_from_session,
)

from ...submissions.api.permissions import ActiveSubmissionPermission
from ...submissions.models import Submission
from ...utils.api.views import ListMixin
from ..constants import FORM_AUTH_SESSION_KEY
from ..registry import register
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


class AuthenticationLogoutView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = (
        serializers.Serializer
    )  # just to shut up some warnings in drf-spectacular

    @extend_schema(
        summary=_("Delete session"),
        description=_(
            "Calling this endpoint will clear the current user session and delete the session cookie."
        ),
        deprecated=True,  # replaced with the submission specific SubmissionLogoutView
    )
    @transaction.atomic()
    def delete(self, request, *args, **kwargs):
        # first, hash all the submissions identifying parameters before flushing
        # the session. These submissions become effectively unreachable (unless there
        # is still a resume link somewhere).
        submissions = get_submissions_from_session(request.session)
        for submission in submissions:
            submission.hash_identifying_attributes()
            submission.save()

        for plugin in register.iter_enabled_plugins():
            plugin.logout(request)

        request.session.flush()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubmissionLogoutView(GenericAPIView):
    authentication_classes = ()
    permission_classes = (ActiveSubmissionPermission,)
    serializer_class = (
        serializers.Serializer
    )  # just to shut up some warnings in drf-spectacular

    queryset = Submission.objects.all()
    lookup_field = "uuid"

    @extend_schema(
        operation_id="submission_session_destroy",
        summary=_("Delete session"),
        description=_(
            "Calling this endpoint will clear the current form and submission from the session."
        ),
    )
    @transaction.atomic()
    def delete(self, request, *args, **kwargs):
        submission = self.get_object()

        remove_submission_from_session(submission, request.session)

        if FORM_AUTH_SESSION_KEY in request.session:
            del request.session[FORM_AUTH_SESSION_KEY]

        if not submission.auth_attributes_hashed:
            submission.hash_identifying_attributes(save=True)

        for plugin in register.iter_enabled_plugins():
            plugin.logout(request)

        return Response(status=status.HTTP_204_NO_CONTENT)
