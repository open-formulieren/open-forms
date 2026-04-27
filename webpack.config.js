const webpack = require('webpack');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CopyPlugin = require('copy-webpack-plugin');
const argv = require('yargs').argv;
const path = require('path');

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
    // Public (end-user facing)
    public: `${__dirname}/src/openforms/js/public.js`,
    'public-styles': `${__dirname}/src/openforms/ui/static/ui/scss/screen.scss`,
    'pdf-css': `${__dirname}/src/openforms/scss/pdf.scss`,
    // Admin-user facing
    admin_overrides: `${__dirname}/src/openforms/scss/admin/admin_overrides.scss`,
    'core-css': `${__dirname}/src/openforms/scss/screen.scss`,
    'core-js': `${__dirname}/src/openforms/js/index.js`,
  },

  // (Output) bundle locations.
  output: {
    path: `${__dirname}/src/openforms/static/bundles/`,
    filename: '[name].js', // file
    chunkFilename: '[name].bundle.js',
    publicPath: '/static/bundles/',
  },

  // Plugins
  plugins: [
    new MiniCssExtractPlugin(),
    new webpack.DefinePlugin({
      STATIC_URL: JSON.stringify(process.env.STATIC_URL ?? '/static/'),
      'process.env.API_BASE_URL': JSON.stringify(process.env.API_BASE_URL ?? ''),
    }),
    new webpack.ProvidePlugin({
      _: 'lodash',
    }),
    // copy leaflet files, replaces gulp action
    new CopyPlugin({
      patterns: [{from: 'node_modules/leaflet/dist/images', to: 'images'}],
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
              url: false,
            },
          },

          // Runs postcss configuration (postcss.config.js).
          {
            loader: 'postcss-loader',
          },

          // Compiles .scss to .css.
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                comments: false,
                style: 'compressed',
              },
              sourceMap: argv.sourcemap,
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
    ],
  },

  resolve: {
    modules: [
      'node_modules',
      path.resolve(__dirname, 'node_modules'),
      path.resolve(__dirname, 'src/openforms/js'),
    ],
  },

  // Use --production to optimize output.
  mode: isProduction ? 'production' : 'development',
  devtool: !isProduction ? 'cheap-module-source-map' : 'source-map',
};
