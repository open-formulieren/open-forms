import re

from decouple import Csv, config as _config, undefined
from sentry_sdk.integrations import DidNotEnable, django, redis

FILE_SIZE_CONVERSIONS = {
    "KiB": lambda val: val << 10,
    "MiB": lambda val: val << 20,
    "KB": lambda val: val * 1_000,
    "MB": lambda val: val * 1_000_000,
}
FILE_SIZE_CONVERSIONS["k"] = FILE_SIZE_CONVERSIONS["KiB"]
FILE_SIZE_CONVERSIONS["K"] = FILE_SIZE_CONVERSIONS["KiB"]
FILE_SIZE_CONVERSIONS["m"] = FILE_SIZE_CONVERSIONS["MiB"]
FILE_SIZE_CONVERSIONS["M"] = FILE_SIZE_CONVERSIONS["MiB"]


class Filesize:
    """
    Cast various filesize notations into an int of bytes.

    Nginx measurement units: https://nginx.org/en/docs/syntax.html and parsing code:
    https://hg.nginx.org/nginx/file/default/src/core/ngx_parse.c. Note that nginx uses
    k/K for kibibytes and m/M for mebibytes (as opposed to kilobytes/megabytes).
    """

    PATTERN = re.compile(r"^(?P<numbers>[0-9]+)(?P<unit>[a-zA-Z]+)?$")

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

        if not (converter := FILE_SIZE_CONVERSIONS.get(unit)):
            raise ValueError(f"Unknown/unsupported unit: '{unit}'")

        return converter(numbers)


def config(option: str, default=undefined, *args, **kwargs):
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
        if default == []:
            default = ""

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
