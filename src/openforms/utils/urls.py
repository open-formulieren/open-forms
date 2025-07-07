from __future__ import annotations

from collections.abc import Callable, Sequence
from importlib import import_module
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.urls import URLPattern, URLResolver, include, reverse
from django.utils.encoding import iri_to_uri
from django.utils.functional import cached_property

from furl import furl

from openforms.typing import AnyRequest

if TYPE_CHECKING:
    from django.conf.urls import _IncludedURLConf


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
    current_scheme_host = f"{base.scheme}://{base.netloc}"

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


class _DecoratedPatterns:
    """
    A wrapper for an urlconf that applies a decorator to all its views.
    """

    # Vendored from https://github.com/twidi/django-decorator-include

    # BSD 2-Clause License

    # Copyright (c) 2016, Jeff Kistler
    # All rights reserved.

    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:

    # * Redistributions of source code must retain the above copyright notice, this
    # list of conditions and the following disclaimer.

    # * Redistributions in binary form must reproduce the above copyright notice,
    # this list of conditions and the following disclaimer in the documentation
    # and/or other materials provided with the distribution.

    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    # AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    # IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
    # FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    # DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    # SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    # CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    # OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    # OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    def __init__(self, urlconf_module, decorators) -> None:
        # ``urlconf_module`` may be:
        #   - an object with an ``urlpatterns`` attribute
        #   - an ``urlpatterns`` itself
        #   - the dotted Python path to a module with an ``urlpatters`` attribute
        self.urlconf = urlconf_module
        try:
            iter(decorators)
        except TypeError:
            decorators = [decorators]
        self.decorators = decorators

    def decorate_pattern(self, pattern):
        if isinstance(pattern, URLResolver):
            decorated = URLResolver(
                pattern.pattern,
                _DecoratedPatterns(pattern.urlconf_module, self.decorators),
                pattern.default_kwargs,
                pattern.app_name,
                pattern.namespace,
            )
        else:
            callback = pattern.callback
            for decorator in reversed(self.decorators):
                callback = decorator(callback)
            decorated = URLPattern(
                pattern.pattern,
                callback,
                pattern.default_args,
                pattern.name,
            )
        return decorated

    @cached_property
    def urlpatterns(self):
        # urlconf_module might be a valid set of patterns, so we default to it.
        patterns = getattr(self.urlconf_module, "urlpatterns", self.urlconf_module)
        return [self.decorate_pattern(pattern) for pattern in patterns]

    @cached_property
    def urlconf_module(self):
        if isinstance(self.urlconf, str):
            return import_module(self.urlconf)
        else:
            return self.urlconf

    @cached_property
    def app_name(self):
        return getattr(self.urlconf_module, "app_name", None)


def decorator_include(
    decorators: Callable[..., Any] | list[Callable[..., Any]],
    arg: Any,
    namespace: str | None = None,
) -> _IncludedURLConf:
    """
    Works like ``django.conf.urls.include`` but takes a view decorator
    or a list of view decorators as the first argument and applies them,
    in reverse order, to all views in the included urlconf.
    """
    if isinstance(arg, tuple) and len(arg) == 3 and not isinstance(arg[0], str):
        # Special case where the function is used for something like `admin.site.urls`, which
        # returns a tuple with the object containing the urls, the app name, and the namespace
        # `include` does not support this pattern (you pass directly `admin.site.urls`, without
        # using `include`) but we have to
        urlconf_module, app_name, namespace = arg
    else:
        urlconf_module, app_name, namespace = include(arg, namespace=namespace)
    return (
        cast(
            Sequence[URLPattern | URLResolver],
            _DecoratedPatterns(urlconf_module, decorators),
        ),
        app_name,
        namespace,
    )
