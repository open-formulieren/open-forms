const gulp = require('gulp');
const {bundle} = require('./bundle');
const {leaflet} = require('./leaflet');

const build = gulp.parallel(bundle, leaflet);

gulp.task('build', build);
exports.build = build;
