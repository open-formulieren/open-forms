'use strict';
var gulp = require('gulp');
var webpack = require('webpack-stream');
var paths = require('../paths');
var webpackConfig = require('../../webpack.config.js');


/**
 * Webpack task
 * Run using "gulp webpack"
 * Runs webpack to compile javascript
 */
function bundle() {
    return gulp.src(`${paths.sourcesRoot}js/index.js`)
        .pipe(webpack(webpackConfig))
            .on('error', function () {
              this.emit('end');
            })
        .pipe(gulp.dest(webpackConfig.output.path));
}

gulp.task('bundle', bundle);
exports.bundle = bundle;
