from typing import Any
from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.urls import reverse
from django.utils.encoding import iri_to_uri

from furl import furl

from openforms.typing import AnyRequest


def build_absolute_uri(location: str, request: AnyRequest | None = None):
    """
    Construct an absolutely qualified URI from a location/path.

    If no request argument is provided, the fully qualified URI is constructed via
    :attr:`settings.BASE_URL`.

    :arg location: the path to make absolute, without protocol, netloc or port number.
      Assumed to be an absolute path.
    :arg request: optionally - the current request object. If provided,
      :meth:`request.build_absolute_uri` is called.
    """
    if request:
        return request.build_absolute_uri(location)

    # copied and modified from request.build_absolute_uri()
    base = urlsplit(settings.BASE_URL)
    current_scheme_host = "{}://{}".format(base.scheme, base.netloc)

    bits = urlsplit(location)
    if not (bits.scheme and bits.netloc):
        # Handle the simple, most common case. If the location is absolute
        # and a scheme or host (netloc) isn't provided, skip an expensive
        # urljoin() as long as no path segments are '.' or '..'.
        if (
            bits.path.startswith("/")
            and not bits.scheme
            and not bits.netloc
            and "/./" not in bits.path
            and "/../" not in bits.path
        ):
            # If location starts with '//' but has no netloc, reuse the
            # schema and netloc from the current request. Strip the double
            # slashes and continue as if it wasn't specified.
            if location.startswith("//"):
                location = location[2:]
            location = current_scheme_host + location
        else:
            # Join the constructed URL with the provided location, which
            # allows the provided location to apply query strings to the
            # base path.
            location = urljoin(current_scheme_host, location)
    return iri_to_uri(location)


def reverse_plus(
    name: str,
    *,
    args=None,
    kwargs=None,
    request: AnyRequest | None = None,
    query: dict[str, Any] | None = None,
    make_absolute: bool = True,
):
    """
    Reverse a named URL with GET query params, absolute URL with internal build_absolute_uri()

    This is both more readable *and* formatter friendly than a local reverse/furl/build_absolute_uri

    If `make_absolute` is True and no `request` argument is provided, the fully qualified URI is constructed via
    :attr:`settings.BASE_URL`.

    :arg name: the URL name to reverse.
    :arg args: optionally - arg-argument to reverse().
    :arg kwargs: optionally - kwargs-argument to reverse().
    :arg request: optionally - the current request object. If provided,
      :meth:`request.build_absolute_uri` is called.
    :arg query: optionally - add key/values as URL GET parameter
    :arg make_absolute: optionally - disable absolute URL
    """
    location = reverse(
        name,
        args=args,
        kwargs=kwargs,
        # additional reverse() arguments could be added when needed
    )
    if make_absolute:
        # use the custom build_absolute_uri()
        location = build_absolute_uri(location, request=request)
    if query:
        f = furl(location)
        f.set(query=query)
        return f.url
    else:
        return location


def is_admin_request(request: AnyRequest) -> bool:
    """
    Checks whether a request is made from the admin

    :arg request: the request object to be checked.
    """
    admin_path_prefix = reverse("admin:index")
    if request.path_info.startswith(admin_path_prefix):
        return True
    if not (referrer := request.headers.get("Referer")):
        return False
    admin_base = request.build_absolute_uri(admin_path_prefix)
    return referrer.startswith(admin_base)
