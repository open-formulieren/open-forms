"""
Concrete view classes/utilities not tied to any particular app.
"""

from collections import OrderedDict

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _

import sentry_sdk
from drf_spectacular.utils import extend_schema
from maykin_common.config import config
from rest_framework import (
    authentication,
    exceptions as drf_exceptions,
    permissions,
    status,
)
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler as drf_exception_handler

from openforms.submissions.api.permissions import AnyActiveSubmissionPermission

from ..exception_handling import HandledException
from ..serializers import ExceptionSerializer

ERR_CONTENT_TYPE = "application/problem+json"


def exception_handler(exc, context):
    """
    Transform 4xx and 5xx errors into DSO-compliant shape.
    """
    response = drf_exception_handler(exc, context)
    if response is None:
        # make it possible to debug failures in CI/local dev environment...
        if config("DEBUG", default=False):
            return None

        sentry_sdk.capture_exception(exc)
        # unkown type, so we use the generic Internal Server Error
        exc = drf_exceptions.APIException("Internal Server Error")
        response = Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    request = context.get("request")

    serializer = HandledException.as_serializer(exc, response, request)
    response.data = OrderedDict(serializer.data.items())
    # custom content type
    response["Content-Type"] = ERR_CONTENT_TYPE
    return response


class PingView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser | AnyActiveSubmissionPermission,)

    @extend_schema(
        summary=_("Ping the API"),
        description=_(
            "Pinging the API extends the user session. Note that you must be "
            "a staff user or have active submission(s) in your session."
        ),
        responses={
            204: None,
            "4XX": ExceptionSerializer,
        },
    )
    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


def health_check_view(request):
    """
    Simple view for making sure that the API is accessible.

    The purpose of the view is to access it only internally so extra permissions and
    authentication is not needed here (DRF complicates things). The real check for what
    has access/permissions to this view is done in the nginx level.
    """
    return HttpResponse(status=204)
