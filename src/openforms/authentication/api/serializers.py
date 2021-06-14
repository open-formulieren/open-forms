from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


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

    class Meta:
        label = _("...")


class LoginOptionSerializer(serializers.Serializer):
    identifier = serializers.CharField(label=_("Identifier"), read_only=True)
    label = serializers.CharField(
        label=_("Button label"), help_text=_("Button label"), read_only=True
    )
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
