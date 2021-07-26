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
        {"foo": ["Invalid data."]}, code="validation-error"
    )


class NotFoundView(BaseErrorView):
    exception = exceptions.NotFound("Some detail message")


class NotAuthenticatedView(BaseErrorView):
    authentication_classes = (authentication.BasicAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    exception = exceptions.NotAuthenticated()


class PermissionDeniedView(BaseErrorView):
    exception = exceptions.PermissionDenied("This action is not allowed")


class MethodNotAllowedView(BaseErrorView):
    exception = exceptions.MethodNotAllowed("GET")


class NotAcceptableView(BaseErrorView):
    exception = exceptions.NotAcceptable("Content negotation failed")


class ConflictView(BaseErrorView):
    exception = Conflict("The resource was updated, please retrieve it again")


class GoneView(BaseErrorView):
    exception = Gone("The resource was destroyed")


class PreconditionFailed(BaseErrorView):
    exception = PreconditionFailed("Something about CRS")


class UnsupportedMediaTypeView(BaseErrorView):
    exception = exceptions.UnsupportedMediaType(
        "application/xml", detail="This media type is not supported"
    )


class ThrottledView(BaseErrorView):
    exception = exceptions.Throttled(detail="Too many requests")


class InternalServerErrorView(BaseErrorView):
    exception = exceptions.APIException("Everything broke")
