const gulp = require('gulp');
const paths = require('../paths');
const {bundle} = require('./bundle');
const {lint} = require('./lint');


/**
 * Watch task
 * Run using "gulp watch"
 */
const watch = gulp.parallel(watchBundles);


/**
 * Watch-js task
 * Run using "gulp watch-js"
 * Runs "bundle" and "lint" tasks instantly and when any file in paths.jsSrc changes
 */
function watchBundles() {
    bundle();
    gulp.watch([paths.jsSrc, paths.jsSpec, paths.scssSrc, `${paths.sourcesRoot}core/static/`], gulp.parallel(bundle, lint));
}



exports.watch = watch;
gulp.task('watch', watch);
