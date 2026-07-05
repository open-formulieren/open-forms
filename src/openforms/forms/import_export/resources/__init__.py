from .base import BaseResource
from .product import ProductResource
from .wms_tile_layer import WMSTileLayerResource
from .wmts_tile_layer import WMTSTileLayerResource
from .yivi_attribute_group import YiviAttributeGroupResource

__all__ = [
    "BaseResource",
    "ProductResource",
    "WMSTileLayerResource",
    "WMTSTileLayerResource",
    "YiviAttributeGroupResource",
]
