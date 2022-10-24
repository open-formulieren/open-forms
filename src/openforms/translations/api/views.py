from django.conf import settings
from django.http import HttpRequest
from django.utils.translation import get_language, get_language_info, gettext_lazy as _

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import LanguageInfoSerializer


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
            }
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
