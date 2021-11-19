import json
import os

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView


# TODO: Optimize this view with sendfile #855
class FormIOTranslationsView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    serializer_class = serializers.Serializer
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary=_("Get FormIO translations"),
        description=_("Retrieve the translations for the strings used by FormIO"),
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
        with open(filepath, "r") as translation_file:
            translations_nl = json.load(translation_file)
        return Response(status=status.HTTP_200_OK, data={"nl": translations_nl})
