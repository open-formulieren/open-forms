from pathlib import Path
from typing import List

from django.conf import settings
from django.http import FileResponse
from django.utils.translation import (
    activate,
    get_language,
    get_language_info,
    gettext_lazy as _,
)

from drf_spectacular.plumbing import build_object_type
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.drf_spectacular.functional import lazy_enum
from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.translations.utils import set_language_cookie

from .serializers import LanguageCodeSerializer, LanguageInfoSerializer


def get_language_codes() -> List[str]:
    return [language[0] for language in settings.LANGUAGES]


class LanguageInfoView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_serializer(self, *args, **kwargs):
        return LanguageInfoSerializer(
            *args,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    @extend_schema(
        summary=_("List available languages and the currently active one."),
        tags=["translations"],
        examples=[
            OpenApiExample(
                "Selected Dutch",
                value={
                    "languages": [
                        {"code": "en", "name": "English"},
                        {"code": "nl", "name": "Nederlands"},
                        # FIXME: code is validated against the enum list, and at the
                        # moment we only support en/nl
                        # {"code": "fy", "name": "frysk"},
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
    permission_classes = ()

    def get_serializer(self, *args, **kwargs):
        return LanguageCodeSerializer(
            *args, context={"request": self.request, "view": self}, **kwargs
        )

    @extend_schema(
        summary=_("Set the desired language"),
        tags=["translations"],
        responses={
            "204": None,
            "400": ValidationErrorSerializer,
            "5XX": ExceptionSerializer,
        },
    )
    def put(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        language_code = serializer.data["code"]
        activate(language_code)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        set_language_cookie(response, language_code)
        return response


@extend_schema(
    summary=_("Get FormIO translations"),
    description=_("Retrieve the translations for the strings used by FormIO."),
    tags=["translations"],
    parameters=[
        OpenApiParameter(
            name="language",
            location=OpenApiParameter.PATH,
            description=_("Language code to retrieve the messages for."),
            type=str,
            enum=lazy_enum(get_language_codes),
        ),
    ],
    responses={
        ("200", "application/json"): build_object_type(
            additionalProperties={"type": "string"}
        ),
        "404": ExceptionSerializer,
        "5XX": ExceptionSerializer,
    },
)
class FormioTranslationsView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def get(self, request, language: str):
        _valid_codes = get_language_codes()
        if language not in _valid_codes:
            raise NotFound(
                _("The language code {language} is not supported.").format(
                    language=language
                )
            )
        filepath = (
            Path(settings.DJANGO_PROJECT_DIR)
            / "js"
            / "lang"
            / "formio"
            / f"{language}.json"
        )
        return FileResponse(filepath.open("rb"))
