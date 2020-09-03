'use strict';
var gulp = require('gulp');
var jshint = require('gulp-jshint');
var paths = require('../paths');


/**
 * Lint task
 * Run using "gulp lint"
 * Runs jshint
 */
function lint() {
    return gulp.src([paths.jsSrc])
        .pipe(jshint())
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('gulp-jshint-jslint-file-reporter', {
            filename: paths.coverageDir + '/jshint-output.xml'
        }));
}

gulp.task('lint', lint);
exports.lint = lint;
