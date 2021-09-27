from django.conf import settings
from django.core.cache import DEFAULT_CACHE_ALIAS

from .constants import NLXDirectories

NLX_DIRECTORY_URLS = {
    NLXDirectories.demo: "https://directory.demo.nlx.io/",
    NLXDirectories.preprod: "https://directory.preprod.nlx.io/",
    NLXDirectories.prod: "https://directory.prod.nlx.io/",
}

NLX_OUTWAY_TIMEOUT = 2  # 2 seconds

ZGW_CONSUMERS_OAS_CACHE = DEFAULT_CACHE_ALIAS

ZGW_CONSUMERS_CLIENT_CLASS = "zgw_consumers.client.ZGWClient"

ZGW_CONSUMERS_TEST_SCHEMA_DIRS = []


def get_setting(name: str):
    default = globals()[name]
    return getattr(settings, name, default)
