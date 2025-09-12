from import_export import resources

from .models import MapWMSTileLayer


class MapWMSTileLayerResource(resources.ModelResource):
    class Meta:
        model = MapWMSTileLayer
        # Use uuid as identifier
        import_id_fields = ("uuid",)
        fields = ("uuid", "name", "url")
