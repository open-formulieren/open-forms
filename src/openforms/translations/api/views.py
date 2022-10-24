from django.conf import settings
from django.utils.translation import get_language_info, get_language

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def info(request):
    codes = (lang[0] for lang in settings.LANGUAGES)
    languages = [
        {"code": code, "name": get_language_info(code)["name_local"]} for code in codes
    ]
    current = get_language()
    return Response({"langauges": languages, "current": current})
