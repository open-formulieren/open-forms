from django.utils.translation import gettext_lazy as _

from furl import furl
from rest_framework import serializers
from rest_framework.reverse import reverse

from openforms.authentication.base import LoginInfo
from openforms.authentication.registry import register as auth_register
from openforms.plugins.api.serializers import PluginBaseSerializer

from ..constants import LogoAppearance


class TextChoiceSerializer(serializers.Serializer):
    # Serialize not just the values (the way ChoiceField does), but the labels too
    value = serializers.CharField()
    label = serializers.CharField()  # type: ignore  # djangorestframework-stubs#158


class AuthPluginSerializer(PluginBaseSerializer):
    # serializer for form builder
    provides_auth = serializers.CharField(
        label=_("Provides authentication attributes"),
        help_text=_("The authentication attribute provided by this plugin."),
    )
    supports_loa_override = serializers.BooleanField(
        label=_("supports loa override"),
        help_text=_(
            "Does the Identity Provider support overriding the minimum "
            "Level of Assurance (LoA) through the authentication request?"
        ),
    )
    assurance_levels = serializers.ListField(
        child=TextChoiceSerializer(),
        label=_("Levels of assurance"),
        help_text=_("The levels of assurance this plugin defines."),
    )


class LoginLogoSerializer(serializers.Serializer):
    title = serializers.CharField(
        label=_("Title"),
        help_text=_("Display title (for accessibility)"),
        read_only=True,
    )
    image_src = serializers.URLField(
        label=_("Image URL"), help_text=_("URL to the logo image"), read_only=True
    )
    href = serializers.URLField(
        label=_("Click URL"),
        help_text=_("Information link to the authentication provider"),
        read_only=True,
    )
    appearance = serializers.ChoiceField(
        choices=LogoAppearance.choices,
        label=_("Login logo appearance"),
        help_text=_("The appearance of the login logo (dark/light)"),
        read_only=True,
    )

    class Meta:
        label = _("...")


class LoginOptionSerializer(serializers.Serializer):
    # serializer for form
    identifier = serializers.CharField(label=_("Identifier"), read_only=True)

    label = serializers.CharField(
        label=_("Button label"), help_text=_("Button label"), read_only=True
    )  # type: ignore  # djangorestframework-stubs#158
    url = serializers.URLField(
        label=_("Login URL"),
        help_text=_(
            "URL to start login flow, expects 'next' GET-parameter with return url"
        ),
        read_only=True,
    )
    logo = LoginLogoSerializer(
        label=_("Optional logo"),
        help_text=_("Optional logo"),
        read_only=True,
        required=False,
    )
    is_for_gemachtigde = serializers.BooleanField(
        label=_("Is for gemachtigde"),
        help_text=_(
            "This authorization method can be used to log in on behalf of another person or company"
        ),
        read_only=True,
    )


class CosignLoginInfoSerializer(LoginOptionSerializer):
    def get_attribute(self, form):
        if not form.has_cosign_enabled:
            return None

        # cosign component but no auth backends is an invalid config that should
        # display a warning in the UI, but we don't have backend constraints for that
        # (yet).
        if not form.authentication_backends:
            return None

        auth_plugin_id = form.authentication_backends[0]
        auth_url = reverse(
            "authentication:start",
            kwargs={
                "slug": form.slug,
                "plugin_id": auth_plugin_id,
            },
            request=self.context["request"],
        )
        next_url = reverse(
            "submissions:find-submission-for-cosign",
            kwargs={"form_slug": form.slug},
            request=self.context["request"],
        )
        auth_page = furl(auth_url)
        auth_page.args.set("next", next_url)

        auth_plugin = auth_register[auth_plugin_id]

        return LoginInfo(
            auth_plugin.identifier,
            auth_plugin.get_label(),
            url=auth_page.url,
            logo=auth_plugin.get_logo(self.context["request"]),
            is_for_gemachtigde=auth_plugin.is_for_gemachtigde,
        )
