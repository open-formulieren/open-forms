/**
 * A form widget to select a location on a Leaflet map.
 */
import {Formio} from 'react-formio';
import DEFAULT_TABS from "./edit/tabs";
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


export default class PdokComponent extends TextFieldComponent {
    static schema(...extend) {
        return TextFieldComponent.schema({
            type: 'pdok',
            label: 'PDOK kaart',
            key: 'pdokMap',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'Pdok Map',
            group: 'advanced',
            icon: 'map',
            weight: 500,
            schema: PdokComponent.schema()
        };
    }

    get defaultSchema() {
        return PdokComponent.schema();
    }

    get emptyValue() {
        return '';
    }

    renderElement(value, index) {
        console.log('In renderElement');
        if(document.querySelector("#leaflet-map")) {
            return document.querySelector("#leaflet-map").outerHTML;
        }
        return super.renderElement(value, index) + '<div id="leaflet-map" style="height:400px"></div>';
    }
    //
    // // TODO Add attach, setValue,  function
    //
    attachElement(element, index) {
        super.attachElement(element, index);

        console.log('In attachElement');

        if (document.querySelector("#leaflet-map").innerHTML) {
            return;
        }

        let map = L.map(document.querySelector("#leaflet-map"), MAP_DEFAULTS);

        const tiles = L.tileLayer(TILE_LAYERS.url, TILE_LAYERS.options);

        map.addLayer(tiles);
    }


    static editForm() {
        return {components: [DEFAULT_TABS]};
    }
}
