import logging  # noqa: TID251 - only used for the log levels
import re
from collections.abc import Callable, MutableMapping
from typing import ClassVar

from sentry_sdk.integrations import DidNotEnable, django, redis
from sentry_sdk.integrations.logging import LoggingIntegration

type ConverterMapping = MutableMapping[str, Callable[[int], int]]

S_SI: ConverterMapping = {
    "B": lambda val: val,
    "KB": lambda val: val * 1_000,
    "MB": lambda val: val * 1_000_000,
    "GB": lambda val: val * 1_000_000_000,
    "KiB": lambda val: val << 10,
    "MiB": lambda val: val << 20,
    "GiB": lambda val: val << 30,
}
S_SI["b"] = S_SI["B"]

S_NGINX: ConverterMapping = {
    "k": S_SI["KiB"],
    "K": S_SI["KiB"],
    "m": S_SI["MiB"],
    "M": S_SI["MiB"],
    "g": S_SI["GiB"],
    "G": S_SI["GiB"],
}

S_BINARY: ConverterMapping = {
    "B": lambda val: val,
    "KB": lambda val: val << 10,
    "MB": lambda val: val << 20,
    "GB": lambda val: val << 30,
}
for key, value in list(S_BINARY.items()):
    S_BINARY[key.lower()] = value


class Filesize:
    """
    Cast various filesize notations into an int of bytes.

    Nginx measurement units: https://nginx.org/en/docs/syntax.html and parsing code:
    https://hg.nginx.org/nginx/file/default/src/core/ngx_parse.c. Note that nginx uses
    k/K for kibibytes and m/M for mebibytes (as opposed to kilobytes/megabytes).
    """

    PATTERN = re.compile(r"^(?P<numbers>[0-9]+)( )*(?P<unit>[a-zA-Z]+)?$")

    S_SI: ClassVar[ConverterMapping] = S_SI
    S_NGINX: ClassVar[ConverterMapping] = S_NGINX
    S_BINARY: ClassVar[ConverterMapping] = S_BINARY

    def __init__(self, system: ConverterMapping | None = None):
        self.system: ConverterMapping = system or {**self.S_SI, **self.S_NGINX}

    def __call__(self, value: str | int) -> int:
        if isinstance(value, int):
            return value

        match = self.PATTERN.match(value)
        if not match:
            raise ValueError(
                f"Value '{value}' does not match the pattern '<size><unit>' or '<size_in_bytes>'"
            )

        numbers, unit = int(match.group("numbers")), match.group("unit")
        if unit is None:
            return numbers

        if not (converter := self.system.get(unit)):
            raise ValueError(f"Unknown/unsupported unit: '{unit}'")

        return converter(numbers)


def get_sentry_integrations() -> list:
    """
    Determine which Sentry SDK integrations to enable.
    """
    default = [
        django.DjangoIntegration(),
        LoggingIntegration(
            level=logging.INFO,  # breadcrumbs
            # do not send any logs as event to Sentry at all - these must be scraped by
            # the (container) infrastructure instead.
            event_level=None,
        ),
        redis.RedisIntegration(),
    ]
    extra = []

    try:
        from sentry_sdk.integrations import celery
    except DidNotEnable:  # happens if the celery import fails by the integration
        pass
    else:
        extra.append(celery.CeleryIntegration())

    return [*default, *extra]


def mute_logging(config: dict) -> None:  # pragma: no cover
    """
    Disable (console) output from logging.

    :arg config: The logging config, typically the django LOGGING setting.
    """

    # set up the null handler for all loggers so that nothing gets emitted
    for name, logger in config["loggers"].items():
        logger["handlers"] = ["null"]
        # don't drop audit logs
        if name == "openforms_audit":
            logger["handlers"] = ["timeline_logger"]

    # some tooling logs to a logger which isn't defined, and that ends up in the root
    # logger -> add one so that we can mute that output too.
    config["loggers"].update(
        {
            "": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
        }
    )
