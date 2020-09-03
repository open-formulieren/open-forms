const gulp = require('gulp');
const {build} = require('./build');

gulp.task('default', build);
exports.default = build;
