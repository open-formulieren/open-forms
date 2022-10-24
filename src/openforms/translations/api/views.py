from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import get_language, get_language_info, gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from openforms.api.serializers import FieldValidationErrorSerializer

from .serializers import LanguageInfoSerializer, LanguageSerializer


@extend_schema(
    summary=_("Available languages and the currently selected one."),
    examples=[
        OpenApiExample(
            "Selected Dutch",
            value={
                "languages": [
                    {"code": "en", "name": "English"},
                    {"code": "nl", "name": "Nederlands"},
                ],
                "current": "nl",
            },
        )
    ],
    responses=LanguageInfoSerializer,
)
@api_view(["GET"])
def info(request: HttpRequest) -> Response:
    codes = (lang[0] for lang in settings.LANGUAGES)
    languages = [
        {"code": code, "name": get_language_info(code)["name_local"]} for code in codes
    ]
    current = get_language()
    return Response({"langauges": languages, "current": current})


@extend_schema(
    summary=_("Set the current langauge"),
    responses={
        "204": None,
        "400": FieldValidationErrorSerializer,
    },
)
@api_view(["PUT"])
def current_language(request: HttpRequest) -> Response:
    lang = LanguageSerializer(data=request.data)
    if lang.is_valid():
        code = lang.data["code"]
        # no need to django.utils.translation.activate; no content to return
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.set_cookie(
            key=settings.LANGUAGE_COOKIE_NAME,
            value=code,
            expires=settings.LANGUAGE_COOKIE_AGE,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            path=settings.LANGUAGE_COOKIE_PATH,
            secure=settings.LANGUAGE_COOKIE_SECURE,
        )
        return response
    error = FieldValidationErrorSerializer(
        data={
            "name": "code",
            "code": lang.errors["code"][0].code,
            "reason": str(lang.errors["code"][0]),
        }
    )
    error.is_valid()
    return Response(error.data, status=status.HTTP_400_BAD_REQUEST)
