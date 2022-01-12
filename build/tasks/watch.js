const gulp = require('gulp');
const paths = require('../paths');
const {bundle} = require('./bundle');


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
    gulp.watch(
        [
            paths.jsSrc,
            paths.jsSpec,
            paths.scssSrc,
            `${paths.sourcesRoot}scss/`,
        ],
        bundle
    );
}



exports.watch = watch;
gulp.task('watch', watch);
