import logging

from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from furl import furl
from rest_framework import permissions, serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import TemplateHTMLRenderer

from openforms.authentication.registry import register
from openforms.forms.models import Form
from openforms.utils.redirect import allow_redirect_url

logger = logging.getLogger(__name__)

# unique name so we don't clobber a parameter on the arbitrary url form is hosted at
BACKEND_OUTAGE_RESPONSE_PARAMETER = "of-auth-problem"


class AuthenticationFlowBaseView(RetrieveAPIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    # these 'endpoints' are not meant to take or return JSON
    parser_classes = (FormParser, MultiPartParser)
    renderer_classes = (TemplateHTMLRenderer,)
    serializer_class = (
        serializers.Serializer
    )  # just to shut up some warnings in drf-spectacular


@extend_schema(
    summary=_("Start authentication flow"),
    description=_(
        "This endpoint is the internal redirect target to start external login flow."
        "\n\nNote that this is NOT a JSON 'endpoint', but rather the browser should be "
        "redirected to this URL and will in turn receive another redirect."
        "\n\nVarious validations are performed:"
        "\n* the form must be live"
        "\n* the `plugin_id` is configured on the form"
        "\n* logging in is required on the form"
        "\n* the `next` parameter must be present"
        "\n* the `next` parameter must match the CORS policy"
    ),
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
            description=_(
                "Identifier of the authentication plugin. Note that this is validated "
                "against the configured available plugins for this particular form."
            ),
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
        OpenApiParameter(
            name="Location",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.URI,
            description=_(
                "URL of the external authentication service where the end-user will "
                "be redirected to. The value is specific to the selected "
                "authentication plugin."
            ),
            response=[302],
            required=True,
        ),
    ],
    responses={
        (200, "text/html"): OpenApiResponse(
            response=str,
            description=_("OK. A login page is rendered."),
        ),
        302: None,
        (400, "text/html"): OpenApiResponse(
            response=str, description=_("Bad request. Invalid parameters were passed.")
        ),
        (404, "text/html"): OpenApiResponse(
            response=str,
            description=_("Not found. The slug did not point to a live form."),
        ),
    },
)
class AuthenticationStartView(AuthenticationFlowBaseView):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    queryset = Form.objects.live()
    register = register

    def get(self, request, slug: str, plugin_id: str):
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


COMMON_RETURN_RESPONSES = {
    302: None,
    (400, "text/html"): OpenApiResponse(
        response=str, description=_("Bad request. Invalid parameters were passed.")
    ),
    (404, "text/html"): OpenApiResponse(
        response=str,
        description=_("Not found. The slug did not point to a live form."),
    ),
    (405, "text/html"): OpenApiResponse(
        response=str,
        description=_(
            "Method not allowed. The authentication plugin requires `POST` or `GET`, "
            "and the wrong method was used."
        ),
    ),
}


@extend_schema(
    summary=_("Return from external login flow"),
    description=_(
        "Authentication plugins call this endpoint in the return step of the "
        "authentication flow. Depending on the plugin, either `GET` or `POST` "
        "is allowed as HTTP method.\n\nTypically authentication plugins will "
        "redirect again to the URL where the SDK is embedded."
        "\n\nVarious validations are performed:"
        "\n* the form must be live"
        "\n* the `plugin_id` is configured on the form"
        "\n* logging in is required on the form"
        "\n* the redirect target must match the CORS policy"
    ),
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
            name="Location",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.URI,
            description=_("URL where the SDK initiated the authentication flow."),
            response=[302],
            required=True,
        ),
        OpenApiParameter(
            name="Allow",
            location=OpenApiParameter.HEADER,
            type=OpenApiTypes.STR,
            description=_("Allowed HTTP method(s) for this plugin."),
            response=True,
            required=True,
        ),
    ],
)
class AuthenticationReturnView(AuthenticationFlowBaseView):
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    queryset = Form.objects.live()
    register = register

    def _handle_return(self, request, slug, plugin_id):
        """
        Handle the return flow after the user provided authentication credentials.

        This can be either directly to us, or via an authentication plugin. This
        method essentially relays the django 'dispatch' to the relevant authentication
        plugin. We must define ``get`` and ``post`` to have them properly show up and
        be documented in the OAS.
        """
        form = self.get_object()
        try:
            plugin = self.register[plugin_id]
        except KeyError:
            return HttpResponseBadRequest("unknown plugin")
        self._plugin = plugin

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
                    "blocked authentication return with non-allowed redirect from "
                    "plugin '%(plugin_id)s' to '%(location)s'",
                    {"plugin_id": plugin_id, "location": location},
                )
                return HttpResponseBadRequest("redirect not allowed")

        return response

    @extend_schema(responses=COMMON_RETURN_RESPONSES)
    def get(self, request, *args, **kwargs):
        return self._handle_return(request, *args, **kwargs)

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={
            (200, "text/html"): OpenApiResponse(
                response=str,
                description=_(
                    "OK. Possibly a form with validation errors is rendered."
                ),
            ),
            **COMMON_RETURN_RESPONSES,
        },
    )
    def post(self, request, *args, **kwargs):
        return self._handle_return(request, *args, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Override allowed methods from DRF APIView to use the plugin method.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        if hasattr(self, "_plugin"):
            response["Allow"] = self._plugin.return_method
        return response
