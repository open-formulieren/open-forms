from pathlib import Path

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.utils.translation import activate, get_language, gettext_lazy as _

from django_sendfile import sendfile
from drf_spectacular.plumbing import (
    build_array_type,
    build_object_type,
)
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework import permissions, status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from openforms.api.drf_spectacular.functional import lazy_enum
from openforms.api.serializers import ExceptionSerializer, ValidationErrorSerializer
from openforms.api.views.mixins import SerializerContextMixin
from openforms.translations.utils import set_language_cookie

from ..models import TranslationsMetaData
from ..utils import (
    get_language_codes,
    get_supported_languages,
)
from .serializers import LanguageCodeSerializer, LanguageInfoSerializer


class LanguageInfoView(SerializerContextMixin, APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return LanguageInfoSerializer(*args, **kwargs)

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
        languages = get_supported_languages()
        current = get_language()
        serializer = self.get_serializer(
            instance={"languages": languages, "current": current}
        )
        return Response(serializer.data)


class SetLanguageView(SerializerContextMixin, APIView):
    authentication_classes = ()
    permission_classes = ()

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return LanguageCodeSerializer(*args, **kwargs)

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
            enum=lazy_enum(get_language_codes),  # pyright: ignore[reportArgumentType]
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


@extend_schema(
    summary=_("Get customized (compiled) translations"),
    description=_(
        "Retrieve the new customized (compiled) translations after changes have been "
        "applied. This is done based on the language code in the path."
    ),
    tags=["translations"],
    parameters=[
        OpenApiParameter(
            name="language_code",
            location=OpenApiParameter.PATH,
            description=_("Language code to retrieve the messages for."),
            type=str,
            enum=lazy_enum(get_language_codes),  # pyright: ignore[reportArgumentType]
        ),
    ],
    responses={
        "200": {
            "oneOf": [
                build_object_type(additionalProperties=False),
                build_object_type(
                    additionalProperties=build_array_type(
                        build_object_type(additionalProperties=True)
                    )
                ),
            ],
        },
        "404": ExceptionSerializer,
        "5XX": ExceptionSerializer,
    },
    examples=[
        OpenApiExample("Empty object", value={}),
        OpenApiExample(
            "Compiled FormatJS example",
            value={
                "skjd8uh": [{"type": 0, "value": "A translated text"}],
                "abc123": [
                    {
                        "type": 6,
                        "options": {
                            "one": [{"type": 0, "value": "1 item"}],
                            "other": [{"type": 0, "value": "{count} items"}],
                        },
                    }
                ],
            },
        ),
    ],
)
class CustomizedCompiledTranslations(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def _get_custom_translations_file_path(self, language_code: str) -> str | None:
        # filter the objects by the received language code and the most recent and
        # successfully processed upload
        translations_metadata = (
            TranslationsMetaData.objects.filter(
                language_code=language_code,
                last_updated__isnull=False,
            )
            .order_by("-last_updated")
            .first()
        )

        # make sure an instance with a compiled asset attached to it exists
        if (
            not translations_metadata
            or not translations_metadata.compiled_asset.storage.exists(
                translations_metadata.compiled_asset.name
            )
        ):
            return None

        return translations_metadata.compiled_asset.path

    def get(self, request, language_code: str, *args, **kwargs):
        _valid_codes = get_language_codes()
        if language_code not in _valid_codes:
            raise NotFound(
                _("The language code {language} is not supported.").format(
                    language=language_code
                )
            )

        compiled_asset_path = self._get_custom_translations_file_path(language_code)

        if not compiled_asset_path:
            return JsonResponse(data={})

        return sendfile(
            request, compiled_asset_path, attachment=True, mimetype="application/json"
        )
