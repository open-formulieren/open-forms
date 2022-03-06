import mimetypes
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urljoin, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import FileSystemStorage

import weasyprint

MOCK_BASE_URL = "https://open-forms.dev"
# we just need any real looking URL for WeasyPrint to be able to apply it's join stuff


class UrlFetcher:

    """
    URL fetcher that skips the network for /static/* files.
    """

    fallback = weasyprint.default_url_fetcher

    def __init__(self):
        static_url = settings.STATIC_URL
        if not urlparse(static_url).netloc:
            static_url = urljoin(MOCK_BASE_URL, settings.STATIC_URL)
        self.static_url = urlparse(static_url)
        self.local_storage = issubclass(
            staticfiles_storage.__class__, FileSystemStorage
        )

    def __call__(self, url: str) -> dict:
        orig_url = url
        url = urlparse(url)
        same_base = (self.static_url.scheme, self.static_url.netloc) == (
            url.scheme,
            url.netloc,
        )
        if (
            self.local_storage
            and same_base
            and url.path.startswith(self.static_url.path)
        ):
            path = PurePosixPath(url.path).relative_to(self.static_url.path)
            # use finders so that it works in dev too, we already check that it's
            # using filesystem storage earlier
            absolute_path = finders.find(path)
            content_type, encoding = mimetypes.guess_type(absolute_path)
            result = dict(
                mime_type=content_type,
                encoding=encoding,
                redirected_url=orig_url,
                filename=path.parts[-1],
            )
            with open(absolute_path, "rb") as f:
                result["file_obj"] = BytesIO(f.read())
            return result
        return self.fallback(orig_url)
