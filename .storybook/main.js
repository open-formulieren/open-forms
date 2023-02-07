const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  stories: ['../src/**/*.stories.mdx', '../src/**/*.stories.@(js|jsx|ts|tsx)'],
  staticDirs: [
    {from: '../static/admin', to: 'admin'},
    {from: '../static/fonts', to: 'fonts'},
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    'storybook-react-intl',
  ],
  framework: '@storybook/react',
  core: {
    builder: 'webpack5',
  },
  webpackFinal: async config => {
    config.resolve.modules = [
      ...(config.resolve.modules || []),
      'node_modules',
      path.resolve(__dirname, '../src/openforms/js'),
    ];

    config.plugins = config.plugins.concat([new MiniCssExtractPlugin()]);

    config.module.rules = config.module.rules.concat([
      // .scss
      {
        test: /\.(sa|sc)ss$/,
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
              // sourceMap: argv.sourcemap,
            },
          },
        ],
      },
    ]);

    return config;
  },
};
