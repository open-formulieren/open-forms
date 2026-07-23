from openforms.config.models import MapTileLayer
from openforms.forms.models import Form

from .base import BaseResource


class WMTSTileLayerResource(BaseResource):
    class Meta:
        model = MapTileLayer
        import_id_fields = ("identifier",)
        fields = ("identifier", "label", "url")
        store_instance = True
        store_row_values = True

    def export_for_form(self, form: Form):
        wmts_tile_layers = []
        for step in form.form_step_map.values():
            for component in step.form_definition.iter_components():
                if component["type"] == "map":
                    wmts_tile_layers.append(component.get("tileLayerIdentifier", ""))

        if len(wmts_tile_layers) == 0:
            return self.export(queryset=[])

        return self.export(
            queryset=MapTileLayer.objects.filter(
                identifier__in=list(set(wmts_tile_layers))
            )
        )
