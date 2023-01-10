from textwrap import dedent

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer

from .serializers import LogicDescriptionSerializer


@extend_schema(
    summary=_("Generate JsonLogic description"),
    tags=["logic"],
    description=_(
        dedent(  # type:ignore
            """
        Generate a more human-readable description of a given JsonLogic expression.

        This endpoint takes into account (optionally) client-provided sub-expression
        descriptions via the ``_meta.description`` path. E.g. an input like:

        ```json
        {
          "==": [
            {"var": "foo"},
            {
                "+": [{"var": "a"}, {"var": "b"}],
                "_meta": {"description": "a + b"},
            },
          ]
        }
        ```

        would result in a description like:

            {{foo}} is equal to a + b

        The input expression must be a valid JsonLogic expression, otherwise the endpoint
        returns HTTP 400 validation errors.
        """
        ).strip()
    ),
    responses={
        status.HTTP_200_OK: LogicDescriptionSerializer,
        status.HTTP_400_BAD_REQUEST: ValidationErrorSerializer,
        "4XX": ExceptionSerializer,
        "5XX": ExceptionSerializer,
    },
)
class GenerateLogicDescriptionView(APIView):
    serializer_class = LogicDescriptionSerializer
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request: Request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
