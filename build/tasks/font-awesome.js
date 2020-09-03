'use strict';
const gulp = require('gulp');
const paths = require('../paths');


/**
 * Font Awesome task
 * Run using "gulp font-awesome"
 * Moves Font Awesome font files to paths.fontDir
 */
function fontAwesome() {
    return gulp.src('node_modules/@fortawesome/fontawesome-free/webfonts/*')
        .pipe(gulp.dest(paths.fontsDir));
}

gulp.task('font-awesome', fontAwesome);
exports.fontAwesome = fontAwesome;
