'use strict';

const gulp = require('gulp');
const paths = require('../paths');

const dest = paths.cssDir + 'images/';

/**
 * Moves Leaflet images to the correct folder
 */
function leaflet() {
    return gulp
        .src('node_modules/leaflet/dist/images/*')
        .pipe(gulp.dest(dest));
}


gulp.task('leaflet', leaflet);
exports.leaflet = leaflet;
