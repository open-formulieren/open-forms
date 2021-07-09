from typing import Optional
from urllib.parse import urlparse

from django.urls import Resolver404, resolve

from openforms.submissions.models import TemporaryFileUpload


def temporary_upload_uuid_from_url(url) -> Optional[str]:
    try:
        match = resolve(urlparse(url)[2])
    except Resolver404:
        return None
    else:
        if match.view_name == "api:submissions:temporary-file":
            return str(match.kwargs["uuid"])
        else:
            return None


def temporary_upload_from_url(url: str) -> Optional[TemporaryFileUpload]:
    uuid = temporary_upload_uuid_from_url(url)
    if not uuid:
        return None
    return TemporaryFileUpload.objects.filter(uuid=uuid).first()
