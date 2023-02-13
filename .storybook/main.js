const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  stories: ['../src/**/*.stories.mdx', '../src/**/*.stories.@(js|jsx|ts|tsx)'],
  staticDirs: [
    {from: '../static/admin', to: 'static/admin'},
    {from: '../static/fonts', to: 'static/fonts'},
    {from: '../static/img', to: 'static/img'},
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

    config.plugins = config.plugins.concat([
      new MiniCssExtractPlugin({
        filename: 'static/bundles/[name].css',
      }),
    ]);

    config.module.rules = config.module.rules.concat([
      // .scss
      {
        test: /\.scss$/,
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
