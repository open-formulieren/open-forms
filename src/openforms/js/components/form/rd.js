// From https://github.com/arbakker/pdok-js-map-examples/blob/master/leaflet-tms-epsg28992/index.js
import * as leaflet from 'leaflet';
import 'proj4leaflet';

/**
 * see "Nederlandse richtlijn tiling"
 * https://www.geonovum.nl/uploads/standards/downloads/nederlandse_richtlijn_tiling_-_versie_1.1.pdf
 */

// Resolution (in pixels per meter) for each zoomlevel
const RES = [
  3440.64, 1720.32, 860.16, 430.08, 215.04, 107.52, 53.76, 26.88, 13.44, 6.72, 3.36, 1.68, 0.84,
  0.42,
];

const RD =
  '+proj=sterea+lat_0=52.15616055555555+lon_0=5.38763888888889+k=0.9999079+x_0=155000+y_0=463000+ellps=bessel+units=m+towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812+no_defs';

const RD_CRS = new leaflet.Proj.CRS('EPSG:28992', RD, {
  resolutions: RES,
  origin: [-285401.92, 903401.92],
  transformation: leaflet.Transformation(-1, 0, -1, 0),
  bounds: leaflet.bounds([-285401.92, 903401.92], [595401.92, 22598.08]),
});

export {RD_CRS};
