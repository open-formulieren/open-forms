import logging
import mimetypes
from io import BytesIO
from pathlib import PurePosixPath
from typing import Optional, Tuple
from urllib.parse import ParseResult, urljoin, urlparse

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.files.storage import FileSystemStorage, default_storage
from django.template.loader import render_to_string

import weasyprint

logger = logging.getLogger(__name__)


class UrlFetcher:

    """
    URL fetcher that skips the network for /static/* files.
    """

    def __init__(self):
        self.static_url = self._get_fully_qualified_url(settings.STATIC_URL)
        is_static_local_storage = issubclass(
            staticfiles_storage.__class__, FileSystemStorage
        )

        self.media_url = self._get_fully_qualified_url(settings.MEDIA_URL)
        is_media_local_storage = issubclass(
            default_storage.__class__, FileSystemStorage
        )

        self.candidates = (
            (self.static_url, staticfiles_storage, is_static_local_storage),
            (self.media_url, default_storage, is_media_local_storage),
        )

    @staticmethod
    def _get_fully_qualified_url(setting: str):
        fully_qualified_url = setting
        if not urlparse(setting).netloc:
            fully_qualified_url = urljoin(settings.BASE_URL, setting)
        return urlparse(fully_qualified_url)

    def __call__(self, url: str) -> dict:
        orig_url = url
        parsed_url = urlparse(url)

        candidate = self.get_match_candidate(parsed_url)
        if candidate is not None:
            base_url, storage = candidate
            path = PurePosixPath(parsed_url.path).relative_to(base_url.path)

            absolute_path = None
            if storage.exists(path):
                absolute_path = storage.path(path)
            elif settings.DEBUG and storage is staticfiles_storage:
                # use finders so that it works in dev too, we already check that it's
                # using filesystem storage earlier
                absolute_path = finders.find(str(path))

            if absolute_path is None:
                logger.error("Could not resolve path '%s'", path)
                return weasyprint.default_url_fetcher(orig_url)

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
        return weasyprint.default_url_fetcher(orig_url)

    def get_match_candidate(
        self, url: ParseResult
    ) -> Optional[Tuple[ParseResult, FileSystemStorage]]:
        for parsed_base_url, storage, is_local_storage in self.candidates:
            if not is_local_storage:
                continue
            same_base = (parsed_base_url.scheme, parsed_base_url.netloc) == (
                url.scheme,
                url.netloc,
            )
            if not same_base:
                continue
            if not url.path.startswith(parsed_base_url.path):
                continue
            return (parsed_base_url, storage)
        return None


def render_to_pdf(template_name: str, context: dict) -> Tuple[str, bytes]:
    """
    Render a (HTML) template to PDF with the given context.
    """
    rendered_html = render_to_string(template_name, context=context)
    html_object = weasyprint.HTML(
        string=rendered_html,
        url_fetcher=UrlFetcher(),
        base_url=settings.BASE_URL,
    )
    pdf: bytes = html_object.write_pdf()
    return rendered_html, pdf
