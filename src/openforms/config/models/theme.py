import uuid as _uuid

from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.utils.fields import SVGOrImageField


class Theme(models.Model):
    """
    A collection of theme information that determines the style of the page rendered.

    Themes build on top of NL Design System principles - they allow you to configure
    a logo, set up the theme classname to use and which stylesheet(s) to apply.

    # XXX: is main_website link also needed?
    """

    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("An easily recognizable name for the theme, used to identify it."),
    )
    uuid = models.UUIDField(
        _("UUID"),
        unique=True,
        default=_uuid.uuid4,
        editable=False,
    )
    organization_name = models.CharField(
        _("organization name"),
        max_length=100,
        blank=True,
        help_text=_(
            "The name of your organization that will be used as label for elements "
            "like the logo. If left blank, the matching configuration option from the "
            "global configuration is used."
        ),
    )
    main_website = models.URLField(
        _("main website link"),
        blank=True,
        help_text=_(
            "URL to the main website. Used for the 'back to municipality website' link. "
            "If left blank, the matching configuration option from the global configuration "
            "is used."
        ),
    )
    favicon = SVGOrImageField(
        _("favicon"),
        upload_to="logo/",
        blank=True,
        help_text=_(
            "Allow the uploading of a favicon, .png .jpg .svg and .ico are compatible. "
            "If left blank, the matching configuration option from the global configuration "
            "is used."
        ),
    )
    # XXX: do not expose this field via the API to non-admin users! There is not
    # sufficient input validation to protect against the SVG attack surface. The SVG
    # is rendered by the browser of end-users.
    #
    # See https://www.fortinet.com/blog/threat-research/scalable-vector-graphics-attack-surface-anatomy
    #
    # * XSS
    # * HTML Injection
    # * XML entity processing
    # * DoS
    logo = SVGOrImageField(
        _("theme logo"),
        upload_to="logo/",
        blank=True,
        help_text=_(
            "Upload the theme/organization logo, visible to users filling out forms. We "
            "advise dimensions around 150px by 75px. SVG's are permitted."
        ),
    )
    email_logo = models.ImageField(
        _("email logo"),
        upload_to="logo/",
        blank=True,
        help_text=_(
            "Upload the email logo, visible to users who receive an email. We "
            "advise dimensions around 150px by 75px. SVG's are not permitted."
        ),
    )

    #
    # Theme configuration
    #
    classname = models.SlugField(
        _("theme CSS class name"),
        blank=True,
        help_text=_("If provided, this class name will be set on the <html> element."),
    )
    stylesheet = models.URLField(
        _("theme stylesheet URL"),
        blank=True,
        max_length=1000,
        validators=[
            RegexValidator(
                regex=r"\.css$",
                message=_("The URL must point to a CSS resource (.css extension)."),
            ),
        ],
        help_text=_(
            "The URL stylesheet with theme-specific rules for your organization. "
            "This will be included as final stylesheet, overriding previously defined styles. "
            "Note that you also have to include the host to the `style-src` CSP directive. "
            "Example value: https://unpkg.com/@utrecht/design-tokens@1.0.0-alpha.20/dist/index.css."
        ),
    )
    stylesheet_file = models.FileField(
        _("theme stylesheet"),
        blank=True,
        upload_to="config/themes/",
        validators=[FileExtensionValidator(allowed_extensions=("css",))],
        help_text=_(
            "A stylesheet with theme-specific rules for your organization. "
            "This will be included as final stylesheet, overriding previously defined styles. "
            "If both a URL to a stylesheet and a stylesheet file have been configured, the "
            "uploaded file is included after the stylesheet URL."
        ),
    )

    # the configuration of the values of available design tokens, following the
    # format outlined in https://github.com/amzn/style-dictionary#design-tokens which
    # is used by NLDS.
    # TODO: validate against the JSON build from @open-formulieren/design-tokens for
    # available tokens.
    # Example:
    # {
    #   "of": {
    #     "card": {
    #       "background-color": {
    #         "value": "fuchsia"
    #       }
    #     }
    #   }
    # }
    #
    design_token_values = models.JSONField(
        _("design token values"),
        blank=True,
        default=dict,
        help_text=_(
            "Values of various style parameters, such as border radii, background "
            "colors... Note that this is advanced usage. Any available but un-specified "
            "values will use fallback default values. See https://open-forms.readthedocs.io/en/latest"
            "/installation/form_hosting.html#run-time-configuration for documentation."
        ),
    )

    class Meta:
        verbose_name = _("theme")
        verbose_name_plural = _("themes")

    def __str__(self):
        return self.name

    def get_classname(self) -> str:
        """
        Use the configured theme classname or fall back to the implicit default.
        """
        return self.classname or "openforms-theme"

    def get_stylesheets(self) -> list[str]:
        """
        Get a list of stylesheet URLs to load.

        If a stylesheet is uploaded, it has higher precedence than the URL.
        """
        urls = []

        if self.stylesheet:
            urls.append(self.stylesheet)

        if self.stylesheet_file:
            urls.append(self.stylesheet_file.url)

        return urls
