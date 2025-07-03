from django.db import models

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class TimestampedTokenPermission(permissions.BasePermission):
    """
    Validate permission to an object based on a timestamped token.

    The token must be generated an checked by the specified token generator. This
    permission class should be used for object-level permissions only, and is intended
    to be subclassed where the token generator object is defined as a class attribute.
    """

    token_generator = None  # subclasses must define this
    token_kwarg = "token"

    def has_object_permission(
        self, request: Request, view: APIView, obj: models.Model
    ) -> bool:
        assert self.token_generator, (
            f'You must specify a token generator on permission class "{self.__class__.__name__}"'
        )
        assert self.token_kwarg in view.kwargs, (
            f"Expected view {view.__class__.__name__} to be called with a URL keyword argument "
            f'named "{self.token_kwarg}". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
        )
        token = view.kwargs[self.token_kwarg]
        return self.token_generator.check_token(obj, token)
