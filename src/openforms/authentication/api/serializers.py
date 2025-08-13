from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.plugins.api.serializers import PluginBaseSerializer

from ..constants import LogoAppearance


class TextChoiceSerializer(serializers.Serializer):
    # Serialize not just the values (the way ChoiceField does), but the labels too
    value = serializers.CharField()
    label = serializers.CharField()  # type: ignore  # djangorestframework-stubs#158


class AuthPluginSerializer(PluginBaseSerializer):
    # serializer for form builder
    provides_auth = serializers.ListField(
        child=serializers.CharField(
            label=_("Provides authentication attributes"),
            help_text=_("The authentication attribute provided by this plugin."),
        ),
        min_length=1,
    )
    schema = serializers.DictField(
        source="configuration_options.display_as_jsonschema",
        default=None,  # Return None for plugins that don't support configuration_options
        label=_("JSON schema"),
        help_text=_("The generated JSON schema for the plugin options."),
    )


class AttributeGroupSerializer(serializers.Serializer):
    # serializer for form builder
    slug = serializers.CharField(
        label=_("Slug"),
        help_text=_("The unique attribute group slug"),
    )
    name = serializers.CharField(
        label=_("Name"),
        help_text=_("The unique attribute group name"),
    )
    description = serializers.CharField(
        label=_("Description"),
        help_text=_("The attribute group description"),
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
