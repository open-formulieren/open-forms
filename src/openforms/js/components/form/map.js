/**
 * A form widget to select a location on a Leaflet map.
 */
import * as L from 'leaflet';
import {Formio} from 'react-formio';

import {
  CLEAR_ON_HIDE,
  DEFAULT_VALUE,
  DESCRIPTION,
  HIDDEN,
  IS_SENSITIVE_DATA,
  KEY,
  LABEL_REQUIRED,
  PRESENTATION,
  TOOLTIP,
} from './edit/options';
import {ADVANCED, REGISTRATION, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {localiseSchema} from './i18n';
import {RD_CRS} from './rd';

const TextFieldComponent = Formio.Components.components.textfield;

const TILES = 'https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard';

const ATTRIBUTION = `
    Kaartgegevens &copy;
    <a href="https://www.kadaster.nl">Kadaster</a> |
    <a href="https://www.verbeterdekaart.nl">Verbeter de kaart</a>
`;

const TILE_LAYERS = {
  url: `${TILES}/EPSG:28992/{z}/{x}/{y}.png`,
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

const EDIT_FORM_TABS = {
  type: 'tabs',
  key: 'tabs',
  components: [
    {
      key: 'basic',
      label: 'Basic',
      components: [
        LABEL_REQUIRED,
        KEY,
        DESCRIPTION,
        TOOLTIP,
        PRESENTATION,
        HIDDEN,
        CLEAR_ON_HIDE,
        {...IS_SENSITIVE_DATA, defaultValue: true},
        {
          type: 'panel',
          title: 'Default map configuration options',
          key: 'defaultMapConfig',
          clearOnHide: true,
          conditional: {
            show: false,
            when: 'useConfigDefaultMapSettings',
            eq: true,
          },
          validate: {
            json: {
              if: [
                {
                  or: [
                    {
                      all: [
                        [{var: 'data.initialCenter.lat'}, {var: 'data.initialCenter.lng'}],
                        {'!!': {var: ''}},
                      ],
                    },
                    {
                      none: [
                        [{var: 'data.initialCenter.lat'}, {var: 'data.initialCenter.lng'}],
                        {'!!': {var: ''}},
                      ],
                    },
                  ],
                },
                true,
                'Longitude and Longitude needs to be both configured or not.',
              ],
            },
            custom:
              'valid = (Boolean(data.initialCenter.lat) === Boolean(data.initialCenter.lng)) ? true: "Longitude and Longitude needs to be both configured or not."',
          },
          components: [
            {
              type: 'number',
              key: 'defaultZoom',
              label: 'Zoom level.',
              description: 'Default zoom level for the leaflet map.',
              validate: {
                integer: true,
                min: TILE_LAYERS.options.minZoom,
                max: TILE_LAYERS.options.maxZoom,
              },
            },
            {
              label: 'Latitude',
              key: 'initialCenter.lat',
              type: 'number',
              requireDecimal: true,
              validate: {
                min: -90,
                max: 90,
                custom:
                  'valid = (Boolean(data.initialCenter.lat) === Boolean(data.initialCenter.lng)) ? true: "Both Latitude and Longitude are required, either fill in the Longitude or delete the current Latitude."',
              },
            },
            {
              label: 'Longitude',
              key: 'initialCenter.lng',
              type: 'number',
              requireDecimal: true,
              validate: {
                min: -180,
                max: 180,
                custom:
                  'valid = (Boolean(data.initialCenter.lat) === Boolean(data.initialCenter.lng)) ? true: "Both Latitude and Longitude are required, either fill in the Latitude or delete the current Longitude."',
              },
            },
          ],
        },
        {
          type: 'checkbox',
          input: true,
          key: 'useConfigDefaultMapSettings',
          label: 'Use globally configured map component settings',
          tooltip:
            'When this is checked, the map component settings configured in the global settings will be used.',
        },
        DEFAULT_VALUE,
      ],
    },
    ADVANCED,
    VALIDATION,
    REGISTRATION,
    TRANSLATIONS,
  ],
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

    const tiles = L.tileLayer(TILE_LAYERS.url, TILE_LAYERS.options);

    map.addLayer(tiles);

    // Set initial marker at center
    let marker = L.marker([52.1326332, 5.291266]).addTo(map);

    map.on('click', e => {
      map.removeLayer(marker);
      marker = L.marker(e.latlng).addTo(map);
    });
  }

  static editForm() {
    return {components: [EDIT_FORM_TABS]};
  }
}
