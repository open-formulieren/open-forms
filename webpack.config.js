const webpack = require('webpack');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CopyPlugin = require("copy-webpack-plugin");
const argv = require('yargs').argv;
const paths = require('./build/paths');


// Set isProduction based on environment or argv.

let isProduction = process.env.NODE_ENV === 'production';
if (argv.production) {
    isProduction = true;
}

/**
 * Webpack configuration
 * Run using "webpack" or "npm run build"
 */
module.exports = {
    // Entry points locations.
    entry: {
        [`${paths.package.name}-css`]: `${__dirname}/${paths.scssEntry}`,
        [`admin_overrides`]:  `${__dirname}/${paths.sourcesRoot}scss/admin/admin_overrides.scss`,
        [`core-css`]:  `${__dirname}/${paths.sourcesRoot}scss/screen.scss`,
        [`core-js`]:  `${__dirname}/${paths.sourcesRoot}js/index.js`,
        'pdf-css': `${__dirname}/${paths.pdfScssEntry}`,
    },

    // (Output) bundle locations.
    output: {
        path: __dirname + '/' + paths.jsDir,
        filename: '[name].js', // file
        chunkFilename: '[name].bundle.js',
        publicPath: '/static/bundles/',
    },

    // Plugins
    plugins: [
        new MiniCssExtractPlugin(),
        new webpack.DefinePlugin({
            STATIC_URL: JSON.stringify(process.env.STATIC_URL ?? '/static/'),
        }),
        new webpack.ProvidePlugin({
            _: 'lodash',
        }),
        // copy leaflet files, replaces gulp action
        new CopyPlugin({
          patterns: [
            { from: 'node_modules/leaflet/dist/images', to: 'images' },
          ],
        }),
    ],

    // Modules
    module: {
        rules: [
            // .js
            {
                test: /.js?$/,
                exclude: /node_modules/,
                loader: 'babel-loader',
            },

            // .scss
            {
                test: /\.(sa|sc|c)ss$/,
                use: [
                    // Writes css files.
                    MiniCssExtractPlugin.loader,

                    // Loads CSS files.
                    {
                        loader: 'css-loader',
                        options: {
                            url: false
                        },
                    },

                    // Runs postcss configuration (postcss.config.js).
                    {
                        loader: 'postcss-loader'
                    },

                    // Compiles .scss to .css.
                    {
                        loader: 'sass-loader',
                        options: {
                            sassOptions: {
                                comments: false,
                                style: 'compressed'
                            },
                            sourceMap: argv.sourcemap
                        },
                    },
                ],
            },

            // .ejs
            {
              test: /\.ejs$/,
              loader: 'ejs-loader',
              options: {
                variable: 'ctx',
                evaluate: /\{%([\s\S]+?)%\}/g,
                interpolate: /\{\{([\s\S]+?)\}\}/g,
                escape: /\{\{\{([\s\S]+?)\}\}\}/g,
              },
            },
        ]
    },

    // Use --production to optimize output.
    mode: isProduction ? 'production' : 'development',

    // Use --sourcemap to generate sourcemap.
    devtool: argv.sourcemap ? 'sourcemap' : false,
};
