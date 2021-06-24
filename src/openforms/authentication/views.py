import logging
from urllib.parse import urlparse, urlunparse

from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.utils.translation import gettext_lazy as _

from corsheaders.conf import conf as cors_conf
from corsheaders.middleware import CorsMiddleware
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from furl import furl
from rest_framework.generics import RetrieveAPIView

from openforms.authentication.registry import register
from openforms.forms.models import Form

logger = logging.getLogger(__name__)

# unique name so we don't clobber a parameter on the arbitrary url form is hosted at
BACKEND_OUTAGE_RESPONSE_PARAMETER = "openforms-authentication-outage"


def origin_from_url(url: str) -> str:
    parts = urlparse(url)
    new = [parts[0], parts[1], "", "", "", ""]
    return urlunparse(new)


def allow_redirect_url(url: str) -> bool:
    cors = CorsMiddleware()
    origin = origin_from_url(url)
    parts = urlparse(url)

    if not cors_conf.CORS_ALLOW_ALL_ORIGINS and not cors.origin_found_in_white_lists(
        origin, parts
    ):
        return False
    else:
        return True


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="slug",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_("Slug identifiying the form."),
        ),
        OpenApiParameter(
            name="plugin_id",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_("Identifier of the authentication plugin."),
        ),
        OpenApiParameter(
            name="next",
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.URI,
            description=_(
                "URL of the form to redirect back to. This URL is validated "
                "against the CORS configuration."
            ),
            required=True,
        ),
    ]
)
@extend_schema_view(
    get=extend_schema(
        summary=_("Start external login flow"),
        description=_(
            "This endpoint is the internal redirect target to start external login flow."
        ),
        responses={200: None, 302: None, 404: None, 405: None},
    )
)
class AuthenticationStartView(RetrieveAPIView):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    queryset = Form.objects.live()
    register = register

    def get(self, request, slug, plugin_id):
        form = self.get_object()
        try:
            plugin = self.register[plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")

        if not form.login_required:
            return HttpResponseBadRequest("login not required")

        if plugin_id not in form.authentication_backends:
            return HttpResponseBadRequest("plugin not allowed")

        form_url = request.GET.get("next")
        if not form_url:
            return HttpResponseBadRequest("missing 'next' parameter")

        if not allow_redirect_url(form_url):
            logger.warning(
                "blocked authentication start with non-allowed redirect to '%(form_url)s'",
                {"form_url": form_url},
            )
            return HttpResponseBadRequest("redirect not allowed")

        try:
            response = plugin.start_login(request, form, form_url)
        except Exception as e:
            logger.exception(
                "authentication exception during 'start_login()' of plugin '%(plugin_id)s'",
                {"plugin_id": plugin_id},
                exc_info=e,
            )
            # append failure parameter and return to form
            f = furl(form_url)
            f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = plugin_id
            return HttpResponseRedirect(f.url)

        return response


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="slug",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_("Slug identifiying the form."),
        ),
        OpenApiParameter(
            name="plugin_id",
            location=OpenApiParameter.PATH,
            type=OpenApiTypes.STR,
            description=_("Identifier of the authentication plugin."),
        ),
    ]
)
@extend_schema_view(
    get=extend_schema(
        summary=_("Return from external login flow"),
        description=_(
            "This endpoint is the internal redirect target when returning from external login flow."
        ),
        responses={200: None, 302: None, 404: None, 405: None},
    ),
    post=extend_schema(
        summary=_("Return from external login flow"),
        description=_(
            "This endpoint is the internal redirect target when returning from external login flow."
        ),
        responses={200: None, 302: None, 404: None, 405: None},
    ),
)
class AuthenticationReturnView(RetrieveAPIView):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    queryset = Form.objects.live()
    register = register

    def dispatch(self, request, slug, plugin_id):
        form = self.get_object()
        try:
            plugin = self.register[plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")

        if not form.login_required:
            return HttpResponseBadRequest("login not required")

        if plugin_id not in form.authentication_backends:
            return HttpResponseBadRequest("plugin not allowed")

        if plugin.return_method.upper() != request.method.upper():
            return HttpResponseNotAllowed([plugin.return_method])

        response = plugin.handle_return(request, form)

        if response.status_code in (301, 302):
            location = response.get("Location", "")
            if location and not allow_redirect_url(location):
                logger.warning(
                    "blocked authentication return with non-allowed redirect from plugin '%(plugin_id)s' to '%(location)s'",
                    {"plugin_id": plugin_id, "location": location},
                )
                return HttpResponseBadRequest("redirect not allowed")

        return response
