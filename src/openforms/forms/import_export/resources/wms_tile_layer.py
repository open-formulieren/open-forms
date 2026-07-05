from openforms.config.models import MapWMSTileLayer
from openforms.forms.models import Form

from .base import BaseResource


class WMSTileLayerResource(BaseResource):
    class Meta:
        model = MapWMSTileLayer
        fields = ("uuid", "name", "url")

    def export_for_form(self, form: Form):
        wms_tile_layers = []
        for step in form.form_step_map.values():
            for component in step.form_definition.iter_components():
                if component["type"] == "map":
                    wms_tile_layers.extend(
                        overlay["uuid"]
                        for overlay in component.get("overlays", [])
                        if overlay["uuid"] != ""
                    )

        if len(wms_tile_layers) == 0:
            return self.export(queryset=[])

        return self.export(
            queryset=MapWMSTileLayer.objects.filter(uuid__in=list(set(wms_tile_layers)))
        )
