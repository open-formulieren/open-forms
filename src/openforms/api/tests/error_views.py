from django.utils.translation import gettext_lazy as _

from rest_framework import authentication, exceptions, permissions
from rest_framework.views import APIView

from ..exceptions import Conflict, Gone, PreconditionFailed


class BaseErrorView(APIView):
    authentication_classes = ()
    permission_classes = ()

    exception = None

    def get(self, request, *args, **kwargs):
        raise self.exception


class ValidationErrorView(BaseErrorView):
    exception = exceptions.ValidationError(
        {"foo": [_("Invalid data.")]}, code="validation-error"
    )


class NotFoundView(BaseErrorView):
    exception = exceptions.NotFound(_("Some detail message"))


class NotAuthenticatedView(BaseErrorView):
    authentication_classes = (authentication.BasicAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    exception = exceptions.NotAuthenticated()


class PermissionDeniedView(BaseErrorView):
    exception = exceptions.PermissionDenied(_("This action is not allowed"))


class MethodNotAllowedView(BaseErrorView):
    exception = exceptions.MethodNotAllowed("GET")


class NotAcceptableView(BaseErrorView):
    exception = exceptions.NotAcceptable(_("Content negotation failed"))


class ConflictView(BaseErrorView):
    exception = Conflict(_("The resource was updated, please retrieve it again"))


class GoneView(BaseErrorView):
    exception = Gone(_("The resource was destroyed"))


class PreconditionFailed(BaseErrorView):
    exception = PreconditionFailed(_("Something about CRS"))


class UnsupportedMediaTypeView(BaseErrorView):
    exception = exceptions.UnsupportedMediaType(
        "application/xml", detail=_("This media type is not supported")
    )


class ThrottledView(BaseErrorView):
    exception = exceptions.Throttled(detail=_("Too many requests"))


class InternalServerErrorView(BaseErrorView):
    exception = exceptions.APIException(_("Everything broke"))
