from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db.models import Model

from openforms.accounts.models import User
from openforms.plugins.plugin import AbstractBasePlugin

if TYPE_CHECKING:
    from stuf.models import StufService

    from .models import TimelineLogProxy


def _create_log(
    object: Model,
    event: str,
    extra_data: dict | None = None,
    plugin: AbstractBasePlugin | None = None,
    error: Exception | None = None,
    tags: list | None = None,
    user: User | None = None,
) -> TimelineLogProxy | None:
    if getattr(settings, "AUDITLOG_DISABLED", False):
        return

    # import locally or we'll get "AppRegistryNotReady: Apps aren't loaded yet."
    from openforms.logging.models import TimelineLogProxy

    if extra_data is None:
        extra_data = dict()
    extra_data["log_event"] = event

    if plugin:
        extra_data["plugin_id"] = plugin.identifier
        extra_data["plugin_label"] = str(plugin.verbose_name)

    if error:
        extra_data["error"] = str(error)

    if isinstance(tags, list):
        for tag in tags:
            extra_data[tag] = True

    if user and not user.is_authenticated:
        # If user is not authenticated (eg. AnonymousUser) we can not
        #   save it on the TimelineLogProxy model
        user = None

    log_entry = TimelineLogProxy.objects.create(
        content_object=object,
        template=f"logging/events/{event}.txt",
        extra_data=extra_data,
        user=user,
    )
    return log_entry


# - - -


def stuf_zds_request(service: StufService, url):
    _create_log(
        service,
        "stuf_zds_request",
        extra_data={"url": url},
    )


def stuf_zds_success_response(service: StufService, url):
    _create_log(
        service,
        "stuf_zds_success_response",
        extra_data={"url": url},
    )


def stuf_zds_failure_response(service: StufService, url):
    _create_log(
        service,
        "stuf_zds_failure_response",
        extra_data={"url": url},
    )


def stuf_bg_request(service: StufService, url):
    _create_log(
        service,
        "stuf_bg_request",
        extra_data={"url": url},
    )


def stuf_bg_response(service: StufService, url):
    _create_log(
        service,
        "stuf_bg_response",
        extra_data={"url": url},
    )
