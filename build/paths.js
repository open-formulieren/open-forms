const fs = require('fs');


/** Parses package.json */
const pkg = JSON.parse(fs.readFileSync('./package.json', 'utf-8'));

/** Src dir */
const sourcesRoot = 'src/' + pkg.name + '/';

/** "Main" static dir */
const staticRoot = sourcesRoot + 'static/';


/**
 * Application path configuration for use in frontend scripts
 */
module.exports = {
    // Parsed package.json
    package: pkg,

    // Src dir
    sourcesRoot: sourcesRoot,

    // "Main" static dir
    staticRoot: staticRoot,

    // Path to the scss entry point
    scssEntry: sourcesRoot + 'scss/screen.scss',

    // Path to the scss (sources) directory
    scssSrcDir: sourcesRoot + 'scss/',

    // Path to the scss (sources) entry point
    scssSrc: sourcesRoot + 'scss/**/*.scss',

    // Path to the (transpiled) css directory
    cssDir: staticRoot + 'bundles/',

    // Path to the fonts directory
    fontsDir: staticRoot + 'fonts/',

    // Path to the js entry point (source)
    jsEntry: sourcesRoot + 'js/index.js',

    // Path to the compatibility js entry point (source)
    swEntry: sourcesRoot + 'js/sw.js',

    // Path to js (sources)
    jsSrc: sourcesRoot + 'js/**/*.js',

    // Path to the js (sources) directory
    jsSrcDir: sourcesRoot + 'js/',

    // Path to the (transpiled) js directory
    jsDir: staticRoot + 'bundles/',

    // Path to js spec (test) files
    jsSpec: sourcesRoot + 'jstests/**/*.spec.js',

    // Path to js spec (test) entry file
    jsSpecEntry: sourcesRoot + 'jstests/index.js',

    // Path to js code coverage directory
    coverageDir: 'reports/jstests/',

    // Path to HTML templates directory
    htmlTemplatesDir: sourcesRoot + 'templates/views',

    // Path to HTML includes directory
    htmlIncludesDir: sourcesRoot + 'templates/components/'
};
