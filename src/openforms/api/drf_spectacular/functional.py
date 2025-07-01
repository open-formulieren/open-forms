from collections.abc import Callable

from django.utils.functional import lazy


def lazy_enum(func: Callable[[], list]) -> Callable[[], list]:
    return lazy(func, list)()
