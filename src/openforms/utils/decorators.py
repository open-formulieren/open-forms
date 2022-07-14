from functools import wraps

from django.views.decorators.cache import never_cache as django_never_cache


def never_cache(view_func):
    """
    Decorator that wraps around Django's never_cache, adding the "Pragma" header.

    Django doesn't add the ``Pragma: no-cache`` header by itself, but it is desired
    by users of Open Forms, so we add it.
    """

    @django_never_cache
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response["Pragma"] = "no-cache"
        return response

    return _wrapped_view_func
