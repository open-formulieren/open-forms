const gulp = require('gulp');
const {bundle} = require('./bundle');

const build = gulp.parallel(bundle);

gulp.task('build', build);
exports.build = build;
