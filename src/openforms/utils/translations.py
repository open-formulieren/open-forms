from functools import partial
from typing import Callable

from django.conf import settings
from django.utils import translation


def get_default(value) -> str:
    return str(value)


def runtime_gettext(literal) -> Callable[[], str]:
    """
    Generate a callable for migration defaults resolving to a translated literal.

    When using literal :func:`gettext` or :func:`gettext_lazy` default values in
    migrations, the defaults are evaluated and frozen in the migration files.

    By using a callable, we can defer this, see
    https://docs.djangoproject.com/en/2.2/topics/migrations/#serializing-values
    """
    func = partial(get_default, literal)
    return func


class ensure_default_language(translation.override):
    """
    If not translation is activated, ensures that the default LANGUAGE_CODE is.
    """

    def __init__(self, **kwargs):
        super().__init__(language=settings.LANGUAGE_CODE, **kwargs)

    def __enter__(self):
        # only set the default if there's no language set
        current = translation.get_language()
        if current is not None:
            self.language = current
        return super().__enter__()
