// From https://github.com/arbakker/pdok-js-map-examples/blob/master/leaflet-tms-epsg28992/index.js
import * as leaflet from 'leaflet';
import 'proj4leaflet';

/**
 * see "Nederlandse richtlijn tiling"
 * https://www.geonovum.nl/uploads/standards/downloads/nederlandse_richtlijn_tiling_-_versie_1.1.pdf
 */

// Resolution (in pixels per meter) for each zoomlevel
const RES = [
    3440.640,
    1720.320,
    860.160,
    430.080,
    215.040,
    107.520,
    53.760,
    26.880,
    13.440,
    6.720,
    3.360,
    1.680,
    0.840,
    0.420,
];


const RD = '+proj=sterea+lat_0=52.15616055555555+lon_0=5.38763888888889+k=0.9999079+x_0=155000+y_0=463000+ellps=bessel+units=m+towgs84=565.2369,50.0087,465.658,-0.406857330322398,0.350732676542563,-1.8703473836068,4.0812+no_defs';


const RD_CRS = new leaflet.Proj.CRS(
    'EPSG:28992',
    RD,
    {
        resolutions: RES,
        origin: [-285401.920, 903401.920],
        transformation: leaflet.Transformation(-1, 0, -1, 0),
        bounds: leaflet.bounds(
            [-285401.920, 903401.920],
            [595401.920, 22598.080]
        ),
    }
);


export { RD_CRS };
