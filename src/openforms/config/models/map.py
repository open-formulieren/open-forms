from django.db import models
from django.utils.translation import gettext_lazy as _


class LeafletMapBackground(models.Model):
    identifier = models.SlugField(
        _("identifier"),
        help_text=_("A unique identifier for the Leaflet map background"),
    )
    url = models.URLField(
        _("background url"),
        help_text=_(
            "URL to the Leaflet map background. Used for the form map components"
        ),
    )
    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_(
            "An easily recognizable name for the background, used to identify it."
        ),
    )

    class Meta:
        verbose_name = _("leaflet map background")
        verbose_name_plural = _("leaflet map backgrounds")
        ordering = ("label",)

    def __str__(self):
        return f"{self.label} ({self.url})"
