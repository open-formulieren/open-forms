from abc import ABC, ABCMeta, abstractmethod
from itertools import chain

from import_export.resources import ModelResource
from tablib import Dataset

from openforms.authentication.contrib.yivi_oidc.constants import (
    PLUGIN_ID as YIVI_PLUGIN_ID,
)
from openforms.authentication.contrib.yivi_oidc.models import AttributeGroup
from openforms.config.models import MapTileLayer, MapWMSTileLayer
from openforms.products.models import Product

from ..models import Form


class CombinedResourceMeta(type(ModelResource), ABCMeta):
    pass


class BaseResource(ABC, ModelResource, metaclass=CombinedResourceMeta):
    @abstractmethod
    def export_for_form(self, form: Form) -> Dataset:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement export_for_form()"
        )


class ProductResource(BaseResource):
    class Meta:
        model = Product
        fields = ("uuid", "name", "price", "information")

    def export_for_form(self, form: Form):
        products = (
            Product.objects.none()
            if not form.product_id  # pyright: ignore[reportAttributeAccessIssue]
            else Product.objects.filter(pk=form.product_id)  # pyright: ignore[reportAttributeAccessIssue]
        )
        return self.export(queryset=products)


class WMSTileLayerResource(BaseResource):
    class Meta:
        model = MapWMSTileLayer
        fields = ("uuid", "name", "url")

    def export_for_form(self, form: Form):
        tile_layer_uuids: set[str] = set()
        for step in form.form_step_map.values():
            for component in step.form_definition.iter_components():
                if component["type"] == "map":
                    tile_layer_uuids.update(
                        overlay["uuid"]
                        for overlay in component.get("overlays", [])
                        if overlay["uuid"] != ""
                    )

        return self.export(
            queryset=MapWMSTileLayer.objects.filter(uuid__in=tile_layer_uuids)
        )


class WMTSTileLayerResource(BaseResource):
    class Meta:
        model = MapTileLayer
        fields = ("identifier", "label", "url")

    def export_for_form(self, form: Form):
        wmts_tile_layer_identifiers: set[str] = set()
        for step in form.form_step_map.values():
            for component in step.form_definition.iter_components():
                if component["type"] == "map" and component.get("tileLayerIdentifier"):
                    wmts_tile_layer_identifiers.add(component["tileLayerIdentifier"])

        return self.export(
            queryset=MapTileLayer.objects.filter(
                identifier__in=wmts_tile_layer_identifiers
            )
        )


class YiviAttributeGroupResource(BaseResource):
    class Meta:
        model = AttributeGroup
        fields = ("uuid", "name", "description", "attributes")

    def export_for_form(self, form: Form):
        yivi_attribute_group_uuids = set(
            chain.from_iterable(
                yivi_backend.options.get("additional_attributes_groups", [])
                for yivi_backend in form.auth_backends.filter(backend=YIVI_PLUGIN_ID)
            )
        )

        return self.export(
            queryset=AttributeGroup.objects.filter(uuid__in=yivi_attribute_group_uuids)
        )
