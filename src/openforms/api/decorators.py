from functools import wraps

from django.conf import settings


def api_headers(view_func):
    """
    Decorator that adds certain HTTP headers to API responses based on django settings.
    """

    @wraps(view_func)
    def _wrapped_view_func(*args, **kwargs):
        response = view_func(*args, **kwargs)
        for header, value in settings.API_HEADERS.items():
            response[header] = value
        return response

    return _wrapped_view_func
