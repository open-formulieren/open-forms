import json
import os

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from drf_spectacular.plumbing import build_object_type
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


class FormIOTranslationsView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary=_("Get FormIO translations"),
        description=_("Retrieve the translations for the strings used by FormIO"),
        request=None,
        responses={
            200: build_object_type(
                properties={
                    "nl": build_object_type(additionalProperties={"type": "string"})
                },
                required=["nl"],
            ),
        },
        deprecated=True,
    )
    def get(self, request, *args, **kwargs):
        filepath = os.path.abspath(
            os.path.join(
                settings.BASE_DIR,
                "src",
                "openforms",
                "js",
                "lang",
                "formio",
                "nl.json",
            )
        )
        with open(filepath) as translation_file:
            translations_nl = json.load(translation_file)
        return Response(status=status.HTTP_200_OK, data={"nl": translations_nl})
