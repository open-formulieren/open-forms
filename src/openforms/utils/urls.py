from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.utils.encoding import iri_to_uri


def build_absolute_uri(location, request=None):
    if request:
        return request.build_absolute_uri(location)

    # copied and modified from request.build_absolute_uri()
    base = urlsplit(settings.BASE_URL)
    current_scheme_host = "{}://{}".format(base.scheme, base.hostname)

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
