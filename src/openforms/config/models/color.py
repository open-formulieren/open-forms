from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from colorfield.fields import ColorField


class RichTextColor(models.Model):
    color = ColorField(
        _("color"),
        format="hex",
        help_text=_("Color in RGB hex format (#RRGGBB)"),
    )
    label = models.CharField(
        _("label"),
        max_length=64,
        help_text=_("Human readable label for reference"),
    )

    class Meta:
        verbose_name = _("text editor color preset")
        verbose_name_plural = _("text editor color presets")
        ordering = ("label",)

    def __str__(self):
        return f"{self.label} ({self.color})"

    def example(self):
        return format_html(
            '<span style="background-color: {};">&nbsp; &nbsp; &nbsp;</span>',
            self.color,
        )

    example.short_description = _("Example")
