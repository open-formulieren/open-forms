from import_export import resources

from .models import MapWFSTileLayer, MapWMSTileLayer


class MapWMSTileLayerResource(resources.ModelResource):
    class Meta:
        model = MapWMSTileLayer
        # Use uuid as identifier
        import_id_fields = ("uuid",)
        fields = ("uuid", "name", "url")


class MapWFSTileLayerResource(resources.ModelResource):
    class Meta:
        model = MapWFSTileLayer
        # Use uuid as identifier
        import_id_fields = ("uuid",)
        fields = ("uuid", "name", "url")
