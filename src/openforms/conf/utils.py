import re
from typing import Any

from decouple import Csv, config as _config, undefined
from sentry_sdk.integrations import DidNotEnable, django, redis

S_SI = {
    "B": lambda val: val,
    "KB": lambda val: val * 1_000,
    "MB": lambda val: val * 1_000_000,
    "GB": lambda val: val * 1_000_000_000,
    "KiB": lambda val: val << 10,
    "MiB": lambda val: val << 20,
    "GiB": lambda val: val << 30,
}
S_SI["b"] = S_SI["B"]

S_NGINX = {
    "k": S_SI["KiB"],
    "K": S_SI["KiB"],
    "m": S_SI["MiB"],
    "M": S_SI["MiB"],
    "g": S_SI["GiB"],
    "G": S_SI["GiB"],
}

S_BINARY = {
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

    S_SI = S_SI
    S_NGINX = S_NGINX
    S_BINARY = S_BINARY

    def __init__(self, system=None):
        self.system = system or {**self.S_SI, **self.S_NGINX}

    def __call__(self, value) -> int:
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


def config(option: str, default: Any = undefined, *args, **kwargs) -> Any:
    """
    Pull a config parameter from the environment.

    Read the config variable ``option``. If it's optional, use the ``default`` value.
    Input is automatically cast to the correct type, where the type is derived from the
    default value if possible.

    Pass ``split=True`` to split the comma-separated input into a list.
    """
    if "split" in kwargs:
        kwargs.pop("split")
        kwargs["cast"] = Csv()
        if isinstance(default, list):
            default = ",".join(default)

    if default is not undefined and default is not None:
        kwargs.setdefault("cast", type(default))
    return _config(option, default=default, *args, **kwargs)


def get_sentry_integrations() -> list:
    """
    Determine which Sentry SDK integrations to enable.
    """
    default = [
        django.DjangoIntegration(),
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
        if name == "flaky_tests":
            continue
        logger["handlers"] = ["null"]

    # some tooling logs to a logger which isn't defined, and that ends up in the root
    # logger -> add one so that we can mute that output too.
    config["loggers"].update(
        {
            "": {"handlers": ["null"], "level": "CRITICAL", "propagate": False},
        }
    )
