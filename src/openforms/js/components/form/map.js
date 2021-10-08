/**
 * A form widget to select a location on a Leaflet map.
 */
import {Formio} from 'react-formio';
import {DEFAULT_SENSITIVE_TABS} from './edit/tabs';
import * as L from 'leaflet';
import { RD_CRS } from './rd';

const TextFieldComponent = Formio.Components.components.textfield;

const TILES = 'https://geodata.nationaalgeoregister.nl/tiles/service';

const ATTRIBUTION = `
    Kaartgegevens &copy;
    <a href="https://www.kadaster.nl">Kadaster</a> |
    <a href="https://www.verbeterdekaart.nl">Verbeter de kaart</a>
`;

const TILE_LAYERS = {
    url: `${TILES}/wmts/brtachtergrondkaart/EPSG:28992/{z}/{x}/{y}.png`,
    options: {
        minZoom: 1,
        maxZoom: 13,
        attribution: ATTRIBUTION,
    },
};


const MAP_DEFAULTS = {
    continuousWorld: true,
    crs: RD_CRS,
    attributionControl: true,
    center: [52.1326332, 5.291266],
    zoom: 3,
};


export default class Map extends TextFieldComponent {
    static schema(...extend) {
        return TextFieldComponent.schema({
            type: 'map',
            label: 'Map',
            key: 'map',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Map',
            icon: 'map',
            weight: 500,
            schema: Map.schema()
        };
    }

    get defaultSchema() {
        return Map.schema();
    }

    get emptyValue() {
        return '';
    }

    renderElement(value, index) {
        return super.renderElement(value, index) + `<div id="map-${this.id}" style="height: 400px; position: relative;"/>`;
    }

    get inputInfo() {
        const info = super.elementInfo();
        // Hide the input element
        info.attr.type = 'hidden';
        return info;
    }

    attachElement(element, index) {
        super.attachElement(element, index);

        // Prevent exception if container is already initialized
        const container = L.DomUtil.get(`map-${this.id}`);
        if (container !== null) {
            container._leaflet_id = null;
        }

        let map = L.map(`map-${this.id}`, MAP_DEFAULTS);

        const tiles = L.tileLayer(TILE_LAYERS.url, TILE_LAYERS.options);

        map.addLayer(tiles);

        // Set initial marker at center
        let marker = L.marker([52.1326332, 5.291266]).addTo(map);

        map.on('click', (e) => {
          map.removeLayer(marker);
          marker = L.marker(e.latlng).addTo(map);
        });
    }

    static editForm() {
        return {components: [DEFAULT_SENSITIVE_TABS]};
    }
}
