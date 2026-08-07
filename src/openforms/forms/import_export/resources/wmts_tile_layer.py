import re

from openforms.config.models import MapTileLayer
from openforms.forms.models import Form

from .base import BaseResource


class WMTSTileLayerResource(BaseResource):
    deep_comparison_fields = ("label", "url")
    identifier_field = "identifier"

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

    def generate_identifier(self, row):
        current_identifier = row["identifier"]

        # In case the identifier already has a numeric suffix, use that as the starting
        # point.
        match = re.match(r"^(.*?)(\d+)?$", current_identifier)
        identifier_base = match.group(1)
        identifier_index = int(match.group(2)) if match.group(2) is not None else 0

        new_identifier = current_identifier
        existing_identifiers = MapTileLayer.objects.values_list("identifier", flat=True)

        while new_identifier in existing_identifiers:
            identifier_index += 1
            new_identifier = "".join((identifier_base, str(identifier_index)))

        return new_identifier
