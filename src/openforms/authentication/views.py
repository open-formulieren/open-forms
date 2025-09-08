import warnings

from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import FormView

import structlog
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from furl import furl
from rest_framework import authentication, permissions, serializers
from rest_framework.generics import RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.request import Request

from openforms.config.templatetags.theme import THEME_OVERRIDE_CONTEXT_VAR
from openforms.forms.models import Form, FormAuthenticationBackend
from openforms.submissions.api.permissions import owns_submission
from openforms.submissions.cosigning import CosignData
from openforms.submissions.models import Submission
from openforms.submissions.serializers import CoSignDataSerializer
from openforms.utils.redirect import allow_redirect_url

from .base import BasePlugin
from .constants import (
    CO_SIGN_PARAMETER,
    FORM_AUTH_SESSION_KEY,
    REGISTRATOR_SUBJECT_SESSION_KEY,
    AuthAttribute,
)
from .exceptions import InvalidCoSignData
from .forms import RegistratorSubjectInfoForm
from .registry import register
from .signals import (
    authentication_logout,
    authentication_success,
    co_sign_authentication_success,
)

logger = structlog.stdlib.get_logger(__name__)

# unique name so we don't clobber a parameter on the arbitrary url form is hosted at
BACKEND_OUTAGE_RESPONSE_PARAMETER = "of-auth-problem"


class AuthenticationFlowBaseView(RetrieveAPIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.AllowAny,)
    # these 'endpoints' are not meant to take or return JSON
    parser_classes = (FormParser, MultiPartParser)
    renderer_classes = (TemplateHTMLRenderer,)
    serializer_class = (
        serializers.Serializer
    )  # just to shut up some warnings in drf-spectacular

    def _validate_co_sign_submission(self, plugin: BasePlugin) -> Submission | None:
        """
        Check if the flow is a co-sign flow and validate the referenced submission.
        """
        request_data = getattr(self.request, self.request.method)
        if not (submission_uuid := request_data.get(CO_SIGN_PARAMETER)):
            return None

        # validate permissions so that people cannot just tinker with UUIDs in URLs
        if not owns_submission(self.request, submission_uuid):
            raise PermissionDenied("invalid submission ID")

        # load the submission object - the return view is expected to validate against tampering
        submission = get_object_or_404(Submission, uuid=submission_uuid)
        assert not submission.co_sign_data, "Submission already has co-sign data!"

        return submission


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
            name=CO_SIGN_PARAMETER,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.UUID,
            description=_(
                "UUID of the submission for which this co-sign authentication applies. "
                "Presence of this parameter marks a flow as a co-sign flow."
            ),
            required=False,
            deprecated=True,
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

    def get(self, request: Request, slug: str, plugin_id: str):
        form = self.get_object()
        with structlog.contextvars.bound_contextvars(
            module="authentication",
            form=str(form.uuid),
            plugin=plugin_id,
        ):
            logger.info("authentication.started")
            try:
                plugin = self.register[plugin_id]
            except KeyError:
                return HttpResponseBadRequest("unknown plugin")
            structlog.contextvars.bind_contextvars(plugin=type(plugin))

            if not plugin.is_enabled:
                return HttpResponseBadRequest("authentication plugin not enabled")

            try:
                authentication_backend = form.auth_backends.get(
                    backend=plugin.identifier
                )
            except FormAuthenticationBackend.DoesNotExist:
                return HttpResponseBadRequest("plugin not allowed")

            # demo plugins should require admin authentication to protect against random
            # people spoofing other people's credentials.
            if plugin.is_demo_plugin and not request.user.is_staff:
                raise PermissionDenied(
                    _("Demo plugins require an active admin session.")
                )

            form_url = request.GET.get("next")
            if not form_url:
                return HttpResponseBadRequest("missing 'next' parameter")

            if not allow_redirect_url(form_url):
                logger.warning(
                    "authentication.start_blocked",
                    reason="disallowed_redirect",
                    redirect_url=form_url,
                )
                return HttpResponseBadRequest("redirect not allowed")

            self._validate_co_sign_submission(plugin)

            if opts_serializer_cls := plugin.configuration_options:
                serializer = opts_serializer_cls(data=authentication_backend.options)
                if not serializer.is_valid():
                    logger.error(
                        "authentication.start_blocked", reason="invalid_options"
                    )
                    f = furl(form_url)
                    f.args[BACKEND_OUTAGE_RESPONSE_PARAMETER] = plugin_id
                    return HttpResponseRedirect(f.url)
                options = serializer.validated_data
            else:
                options = {}

            logger.info("authentication.call_plugin")
            try:
                response = plugin.start_login(request, form, form_url, options)
            except Exception as exc:
                logger.exception("authentication.start_failure", exc_info=exc)
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
            name=CO_SIGN_PARAMETER,
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.UUID,
            description=_(
                "UUID of the submission for which this co-sign authentication applies. "
                "Presence of this parameter marks a flow as a co-sign flow."
            ),
            required=False,
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

    def _handle_return(self, request: Request, slug: str, plugin_id: str):
        """
        Handle the return flow after the user provided authentication credentials.

        This can be either directly to us, or via an authentication plugin. This
        method essentially relays the django 'dispatch' to the relevant authentication
        plugin. We must define ``get`` and ``post`` to have them properly show up and
        be documented in the OAS.
        """
        form = self.get_object()
        with structlog.contextvars.bound_contextvars(
            module="authentication",
            form=str(form.uuid),
            plugin=plugin_id,
        ):
            logger.info("authentication.return")

            try:
                plugin = self.register[plugin_id]
            except KeyError:
                return HttpResponseBadRequest("unknown plugin")
            self._plugin = plugin
            structlog.contextvars.bind_contextvars(plugin=type(plugin))

            try:
                authentication_backend = form.auth_backends.get(
                    backend=plugin.identifier
                )
            except FormAuthenticationBackend.DoesNotExist:
                return HttpResponseBadRequest("plugin not allowed")

            if plugin.return_method.upper() != request.method.upper():
                return HttpResponseNotAllowed([plugin.return_method])

            # demo plugins should require admin authentication to protect against random
            # people spoofing other people's credentials.
            if plugin.is_demo_plugin and not request.user.is_staff:
                raise PermissionDenied(
                    _("Demo plugins require an active admin session.")
                )

            try:
                self._handle_co_sign(form, plugin)
            except serializers.ValidationError:
                return HttpResponseBadRequest("plugin returned invalid data")
            except InvalidCoSignData as exc:
                return HttpResponseBadRequest(exc.args[0])

            # we can be more brazen, since ending up in the return flow implies the
            # start flow was successful
            if opts_serializer_cls := plugin.configuration_options:
                serializer = opts_serializer_cls(data=authentication_backend.options)
                serializer.is_valid(raise_exception=True)
                options = serializer.validated_data
            else:
                options = {}

            response = plugin.handle_return(
                request,
                form,
                options,
            )

            if response.status_code in (301, 302):
                location = response.get("Location", "")
                if location and not allow_redirect_url(location):
                    logger.warning(
                        "authentication.return_blocked",
                        reason="disallowed_redirect",
                        redirect_url=location,
                    )
                    return HttpResponseBadRequest("redirect not allowed")

            if hasattr(request, "session") and FORM_AUTH_SESSION_KEY in request.session:
                authentication_success.send(sender=self.__class__, request=request)

        return response

    def _handle_co_sign(self, form: Form, plugin: BasePlugin) -> None:
        co_sign_submission = self._validate_co_sign_submission(plugin)
        if co_sign_submission is not None:
            warnings.warn(
                "Legacy co-sign is deprecated and will be removed in Open Forms 4.0",
                DeprecationWarning,
                stacklevel=2,
            )
            logger.debug("handle_co_sign")
            auth_attributes = plugin.provides_auth
            assert len(auth_attributes) == 1
            co_sign_data: CosignData = {
                **plugin.handle_co_sign(self.request, form),
                "version": "v1",
                "plugin": plugin.identifier,
                "co_sign_auth_attribute": auth_attributes[0],
            }
            serializer = CoSignDataSerializer(data=co_sign_data)
            serializer.is_valid(raise_exception=True)

            co_sign_submission.co_sign_data = serializer.validated_data
            co_sign_submission.save(update_fields=["co_sign_data"])

            co_sign_authentication_success.send(
                sender=self.__class__,
                request=self.request,
                plugin=plugin,
                submission=co_sign_submission,
            )

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


class RegistratorSubjectInfoView(PermissionRequiredMixin, FormView):
    form_class = RegistratorSubjectInfoForm
    template_name = "of_authentication/registrator_subject_info.html"
    permission_required = ["of_authentication.can_register_customer_submission"]

    # block the AccessMixin login redirection
    raise_exception = True

    cleaned_next_url = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assert self.cleaned_next_url
        path = str(furl(self.cleaned_next_url).path)
        resolved = resolve(path)
        form = get_object_or_404(Form, slug=resolved.kwargs.get("slug"))
        context[THEME_OVERRIDE_CONTEXT_VAR] = form.theme
        return context

    def dispatch(self, request, *args, **kwargs):
        next_url = self.request.GET.get("next")
        if not next_url or not allow_redirect_url(next_url):
            return HttpResponseBadRequest("missing or bad redirect")

        # save this
        self.cleaned_next_url = next_url
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        skip_subject = form.cleaned_data.get("skip_subject", False)
        if skip_subject:
            self.request.session[REGISTRATOR_SUBJECT_SESSION_KEY] = {
                "skipped_subject_info": True,
            }
        else:
            if form.cleaned_data["bsn"]:
                self.request.session[REGISTRATOR_SUBJECT_SESSION_KEY] = {
                    "value": form.cleaned_data["bsn"],
                    "attribute": AuthAttribute.bsn,
                }
            elif form.cleaned_data["kvk"]:
                self.request.session[REGISTRATOR_SUBJECT_SESSION_KEY] = {
                    "value": form.cleaned_data["kvk"],
                    "attribute": AuthAttribute.kvk,
                }
            elif REGISTRATOR_SUBJECT_SESSION_KEY in self.request.session:
                del self.request.session[REGISTRATOR_SUBJECT_SESSION_KEY]

        assert self.cleaned_next_url
        return HttpResponseRedirect(self.cleaned_next_url)


class AuthPluginLogoutView(UserPassesTestMixin, View):
    http_method_names = ["post"]
    raise_exception = True

    def test_func(self):
        return FORM_AUTH_SESSION_KEY in self.request.session

    def post(self, request, *args, **kwargs):
        auth_info = request.session[FORM_AUTH_SESSION_KEY]

        plugin = register[auth_info["plugin"]]
        plugin.logout(request=request)

        authentication_logout.send(sender=self.__class__, request=request)

        return HttpResponseRedirect(reverse("authentication:logout-confirmation"))


class AuthPluginLogoutConfirmationView(TemplateView):
    template_name = "of_authentication/logout_confirmation.html"
