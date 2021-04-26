/**
 * A form widget to select a location on a Leaflet map.
 */
import {Formio} from 'formiojs';
import {defineEditFormTabs, defineInputInfo} from './../abstract';

import * as L from 'leaflet';

import { RD_CRS } from './rd';

const TextFieldComponent = Formio.Components.components.textfield;
const HiddenComponent = Formio.Components.components.hidden;
// const Component = Formio.Components.components.component;

// delete L.Icon.Default.prototype._getIconUrl
// L.Icon.Default.mergeOptions({
//     iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
//     iconUrl: require('leaflet/dist/images/marker-icon.png'),
//     shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
// });


const TILES = 'https://geodata.nationaalgeoregister.nl/tiles/service';
const ATTRIBUTION = `
    Kaartgegevens &copy;
    <a href="https://www.kadaster.nl">Kadaster</a> |
    <a href="https://www.verbeterdekaart.nl">Verbeter de kaart</a>
`;

const TILE_LAYERS = {
    brt: {
        url: `${TILES}/wmts/brtachtergrondkaart/EPSG:28992/{z}/{x}/{y}.png`,
        options: {
            minZoom: 1,
            maxZoom: 13,
            attribution: ATTRIBUTION,
        },
    },
};


const MAP_DEFAULTS = {
    continuousWorld: true,
    crs: RD_CRS,
    attributionControl: true,
};

// export default class PDOKMap extends TextFieldComponent {
//   static schema(...extend) {
//     return TextFieldComponent.schema({
//       type: 'pdokMap',
//       label: 'PDOK kaart',
//       key: 'pdokMap',
//       map: {
//         key: '',
//         region: '',
//         gmapId: '',
//         autocompleteOptions: {}
//       }
//     }, ...extend);
//   }

//   static get builderInfo() {
//     return {
//       title: 'PDOK kaart',
//       group: 'advanced',
//       icon: 'map',
//       weight: 500,
//       schema: PDOKMap.schema()
//     };
//   }

//   init() {
//     super.init();
//     // Get the source for Google Maps API
//     let src = 'https://maps.googleapis.com/maps/api/js?v=3&libraries=places&callback=googleMapsCallback';
//     if (this.component.map && this.component.map.key) {
//       src += `&key=${this.component.map.key}`;
//     }
//     if (this.component.map && this.component.map.region) {
//       src += `&region=${this.component.map.region}`;
//     }
//     Formio.requireLibrary('googleMaps', 'google.maps.places', src);
//   }

//   get defaultSchema() {
//     return PDOKMap.schema();
//   }

//   get emptyValue() {
//     return '';
//   }

//   get inputInfo() {
//     const info = super.inputInfo;
//     info.attr.class += ' Gmap-search';
//     return info;
//   }

//   renderElement(value, index) {
//     return super.renderElement(value, index) + this.renderTemplate('map', {
//       mapId: this.component.map.gmapId,
//     });
//   }

//   attach(element) {
//     const ret = super.attach(element);
//     this.loadRefs(element, { gmapElement: 'multiple' });
//     return ret;
//   }

//   attachElement(element, index) {
//     super.attachElement(element, index);
//     Formio.libraryReady('googleMaps').then(() => {
//       const defaultLatlng = new google.maps.LatLng(45.5041482, -73.5574125);
//       const options = {
//         zoom: 19,
//         center: defaultLatlng,
//         mapTypeId: google.maps.MapTypeId.ROADMAP,
//         styles: [
//           {
//             'featureType': 'poi',
//             'stylers': [
//               {
//                 'visibility': 'off'
//               }
//             ]
//           },
//           {
//             'featureType': 'transit',
//             'stylers': [
//               {
//                 'visibility': 'off'
//               }
//             ]
//           }
//         ]
//       };

//       if (!this.refs.gmapElement[index]) {
//         return;
//       }
//       element.map = new google.maps.Map(this.refs.gmapElement[index], options);
//       this.addMarker(defaultLatlng, 'Default Marker', element);

//       let autocompleteOptions = {};
//       if (this.component.map) {
//         autocompleteOptions = this.component.map.autocompleteOptions || {};
//       }
//       const autocomplete = new google.maps.places.Autocomplete(element, autocompleteOptions);
//       autocomplete.addListener('place_changed', () => {
//         const place = autocomplete.getPlace();
//         if (!place.geometry) {
//           console.log('Autocomplete\'s returned place contains no geometry');
//           return;
//         }

//         // If the place has a geometry, then present it on a map.
//         if (place.geometry.viewport) {
//           element.map.fitBounds(place.geometry.viewport);
//         }
//         else {
//           element.map.setCenter(place.geometry.location);
//           element.map.setZoom(17);  // Why 17? Because it looks good.
//         }
//         element.marker.setIcon(/** @type {google.maps.Icon} */({
//           url: place.icon,
//           size: new google.maps.Size(71, 71),
//           origin: new google.maps.Point(0, 0),
//           anchor: new google.maps.Point(17, 34),
//           scaledSize: new google.maps.Size(35, 35)
//         }));
//         element.marker.setPosition(place.geometry.location);
//         this.setValue(place.name);
//       });
//     });
//   }

//   setValue(value, flags) {
//     flags = this.getFlags.apply(this, arguments);
//     flags.noValidate = true;
//     super.setValue(value, flags);
//   }

//   addMarker(latlng, title, element) {
//     element.marker = new google.maps.Marker({
//       position: latlng,
//       map: element.map,
//       title: title,
//       draggable:true
//     });
//     element.marker.addListener('dragend', (event) => {
//       const geocoder = new google.maps.Geocoder;
//       const latlng = { lat: parseFloat(event.latLng.lat()), lng: parseFloat(event.latLng.lng()) };
//       geocoder.geocode({ 'location': latlng }, (results, status) => {
//         if (status === google.maps.GeocoderStatus.OK) {
//           if (results[1]) {
//             this.setValue(results[0].formatted_address);
//           }
//           else {
//             console.log('No results found');
//           }
//         }
//         else {
//           console.log(`Geocoder failed due to: ${status}`);
//         }
//       });
//     });
//   }
// }

export default class PDOKMap extends HiddenComponent {
    static schema(...extend) {
        return HiddenComponent.schema({
            type: 'pdokMap',
            label: 'PDOK kaart',
            key: 'pdokMap',
            // map: {
            //   key: '',
            //   region: '',
            //   gmapId: '',
            //   autocompleteOptions: {}
            // }
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'PDOK kaart',
            group: 'advanced',
            icon: 'map',
            weight: 500,
            schema: PDOKMap.schema()
        };
    }

    get defaultSchema() {
        return PDOKMap.schema();
    }

    get emptyValue() {
        return '';
    }

    renderElement(value, index) {
        if(document.querySelector("#leaflet-map")) {
            return document.querySelector("#leaflet-map").outerHTML
        }
        console.log(super.renderElement(value, index))
        return super.renderElement(value, index) + '<div id="leaflet-map" style="height:400px"></div>'
    }


    attachElement(element, index) {
        super.attachElement(element, index);

        if (document.querySelector("#leaflet-map").innerHTML) {
            return;
        }

        const tiles = L.tileLayer(
            TILE_LAYERS["brt"].url,
            TILE_LAYERS["brt"].options
        );


        // let accessToken = "pk.eyJ1IjoiYWxleGRlbGFuZGdyYWFmIiwiYSI6ImNraDB6Nm5hdDA5ZGoycXFmeHFub2YxeWwifQ.vI27Y1BXTv7P0O84NrgFvw";
        // let tiles = L.tileLayer(`https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=${accessToken}`, {
        //     attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
        //     maxZoom: 18,
        //     id: 'mapbox/streets-v11',
        //     tileSize: 512,
        //     zoomOffset: -1,
        //     accessToken: 'your.mapbox.access.token'
        // })

        let map = L.map("leaflet-map", MAP_DEFAULTS).setView([52.0907, 5.1214], 13);
        map.addLayer(tiles);

        let marker;

        map.addEventListener("click", (e) => {
            if(marker) map.removeLayer(marker);
            marker = new L.marker(
                e.latlng,
                // {
                //     rotationAngle: -45,
                //     icon: L.divIcon({
                //         className: 'marker-icon',
                //         popupAnchor: [0, -30]
                //     }),
                //     title: ""
                // }
            ).addTo(map);
        });
    }

    // getValue() {
    //     return super.getValue()
    //     // var value = [];
    //     // for (var rowIndex in this.checks) {
    //     //     var row = this.checks[rowIndex];
    //     //     value[rowIndex] = [];
    //     //     for (var colIndex in row) {
    //     //         var col = row[colIndex];
    //     //         value[rowIndex][colIndex] = !!col.checked;
    //     //     }
    //     // }
    //     // return value;
    // }

    // setValue(value, flags) {
    //     // flags = this.getFlags.apply(this, arguments);
    //     // flags.noValidate = true;
    //     super.setValue(value, flags);
    // }

}

defineEditFormTabs(PDOKMap, [
    {
        type: 'tabs',
        key: 'tabs',
        components: [
            {
                key: 'basic',
                'label': 'Basic',
                components: [
                    {'type': 'textfield', key: 'label', label: 'Label'},
                ]
            }
        ]
    }
]);


Formio.registerComponent('pdokMap', PDOKMap);
