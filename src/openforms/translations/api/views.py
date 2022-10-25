from django.conf import settings
from django.utils.translation import get_language, get_language_info, gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.serializers import ValidationErrorSerializer

from .serializers import LanguageCodeSerializer, LanguageInfoSerializer


class LanguageInfoView(APIView):
    authentication_classes = ()

    def get_serializer(self, *args, **kwargs):
        return LanguageInfoSerializer(
            *args,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    @extend_schema(
        summary=_("List available languages and the currently active one."),
        examples=[
            OpenApiExample(
                "Selected Dutch",
                value={
                    "languages": [
                        {"code": "en", "name": "English"},
                        {"code": "nl", "name": "Nederlands"},
                        {"code": "fy", "name": "frysk"},
                    ],
                    "current": "nl",
                },
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        codes = (lang[0] for lang in settings.LANGUAGES)
        languages = [
            {"code": code, "name": get_language_info(code)["name_local"]}
            for code in codes
        ]
        current = get_language()
        serializer = self.get_serializer(
            instance={"languages": languages, "current": current}
        )
        return Response(serializer.data)


class SetLanguageView(APIView):
    authentication_classes = ()

    @extend_schema(
        summary=_("Set the desired language"),
        request=LanguageCodeSerializer,
        responses={
            "204": None,
            "400": ValidationErrorSerializer,
        },
    )
    def put(self, request: Request) -> Response:
        lang = LanguageCodeSerializer(data=request.data)
        if lang.is_valid(raise_exception=True):
            # no need to django.utils.translation.activate; no content to return
            response = Response(status=status.HTTP_204_NO_CONTENT)
            response.set_cookie(
                key=settings.LANGUAGE_COOKIE_NAME,
                value=lang.data["code"],
                max_age=settings.LANGUAGE_COOKIE_AGE,
                domain=settings.LANGUAGE_COOKIE_DOMAIN,
                httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                path=settings.LANGUAGE_COOKIE_PATH,
                samesite=settings.LANGUAGE_COOKIE_SAMESITE,
                secure=settings.LANGUAGE_COOKIE_SECURE,
            )
            return response
