/**
 * A form widget to select a location on a Leaflet map.
 */
import {CRS_RD, TILE_LAYER_RD} from '@open-formulieren/leaflet-tools';
import * as L from 'leaflet';
import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const TextFieldComponent = Formio.Components.components.textfield;

const MAP_DEFAULTS = {
  continuousWorld: true,
  crs: CRS_RD,
  attributionControl: true,
  center: [52.1326332, 5.291266],
  zoom: 3,
};

export default class Map extends TextFieldComponent {
  static schema(...extend) {
    const schema = TextFieldComponent.schema(
      {
        type: 'map',
        label: 'Map',
        key: 'map',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Map',
      icon: 'map',
      weight: 500,
      schema: Map.schema(),
    };
  }

  get defaultSchema() {
    return Map.schema();
  }

  get emptyValue() {
    return '';
  }

  renderElement(value, index) {
    const inputRender = super.renderElement(value, index);
    return `${inputRender}<div id="map-${this.id}" style="height: 400px; position: relative;"></div>`;
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

    const map = L.map(`map-${this.id}`, MAP_DEFAULTS);

    const {url: tileUrl, ...options} = TILE_LAYER_RD;
    const tiles = L.tileLayer(tileUrl, options);
    map.addLayer(tiles);
  }
}
