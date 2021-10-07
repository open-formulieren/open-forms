/**
 * A form widget to select a location on a Leaflet map.
 */
import {Formio} from 'react-formio';
import DEFAULT_TABS from "./edit/tabs";
import * as L from 'leaflet';
import { RD_CRS } from './rd';

// Using Hidden Component so we don't get anything 'extra' with our map
const HiddenComponent = Formio.Components.components.hidden;

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


export default class PdokComponent extends HiddenComponent {
    static schema(...extend) {
        return HiddenComponent.schema({
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
        return super.renderElement(value, index) + `<div id="the-pdok-map-${this.id}" style="height: 400px; position: relative;"/>`;
    }
    //
    // TODO Add attach, setValue functions
    //
    attachElement(element, index) {
        super.attachElement(element, index);

        console.log('In attachElement');

        let map = L.map(document.querySelector("#leaflet-map"), MAP_DEFAULTS);

        const tiles = L.tileLayer(TILE_LAYERS.url, TILE_LAYERS.options);

        map.addLayer(tiles);
    }

    // TODO Probably need more custom tabs than these
    static editForm() {
        return {components: [DEFAULT_TABS]};
    }
}
