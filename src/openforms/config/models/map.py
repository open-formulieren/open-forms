from __future__ import annotations

import uuid as _uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from autoslug import AutoSlugField


class MapTileLayerManager(models.Manager["MapTileLayer"]):
    def get_by_natural_key(self, identifier: str) -> MapTileLayer:
        return self.get(identifier=identifier)


class MapTileLayer(models.Model):
    identifier = AutoSlugField(
        _("identifier"),
        populate_from="label",
        unique=True,
        editable=True,
        max_length=100,
        help_text=_("A unique identifier for the tile layer."),
    )
    url = models.URLField(
        _("tile layer url"),
        max_length=255,
        help_text=_(
            "URL to the tile layer image, used to define the map component "
            "background. To ensure correct functionality of the map, "
            "EPSG 28992 projection should be used. "
            "Example value: https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:28992/{z}/{x}/{y}.png"
        ),
    )
    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_(
            "An easily recognizable name for the tile layer, used to identify it."
        ),
    )

    objects = MapTileLayerManager()

    class Meta:
        verbose_name = _("map tile layer")
        verbose_name_plural = _("map tile layers")
        ordering = ("label",)

    def __str__(self):
        return self.label

    def natural_key(self):
        return (self.identifier,)


class MapWMSTileLayerManager(models.Manager["MapWMSTileLayer"]):
    def get_by_natural_key(self, uuid: str) -> MapWMSTileLayer:
        return self.get(uuid=uuid)


class MapWMSTileLayer(models.Model):
    uuid = models.UUIDField(
        _("UUID"),
        unique=True,
        default=_uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_(
            "An easily recognizable name for the WMS tile layer, used to identify it."
        ),
    )
    url = models.URLField(
        _("tile layer url"),
        max_length=255,
        help_text=_(
            "URL to collect the WMS tile layer capabilities. To ensure correct "
            "functionality of the map, EPSG 28992 projection should be available on the "
            "WMS tile layer. Example value: "
            "https://service.pdok.nl/lv/bag/wms/v2_0?request=getCapabilities&service=WMS"
        ),
        # TODO: add validator?
    )

    objects = MapWMSTileLayerManager()

    class Meta:
        verbose_name = _("WMS layer")
        verbose_name_plural = _("WMS layers")

    def __str__(self):
        return self.name

    def natural_key(self):
        return (self.uuid,)
