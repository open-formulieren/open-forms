import type {StorybookConfig} from '@storybook/react-vite';

const config: StorybookConfig = {
  core: {
    disableTelemetry: true,
    disableWhatsNewNotifications: true,
  },
  stories: ['../src/openforms/js/**/*.mdx', '../src/openforms/js/**/*.stories.@(js|jsx|ts|tsx)'],
  staticDirs: [
    {from: '../static/admin', to: 'static/admin'},
    {from: '../static/fonts', to: 'static/fonts'},
    {from: '../static/img', to: 'static/img'},
    {from: '../static/tinymce', to: 'static/tinymce'},
    // required in dev mode due to style-loader usage
    {from: '../static/admin', to: 'admin'},
    {from: '../static/fonts', to: 'fonts'},
    {from: '../static/img', to: 'img'},
    {from: '../public', to: ''},
  ],
  addons: ['@storybook/addon-links', 'storybook-react-intl', '@storybook/addon-docs'],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  env: config => ({
    ...config,
    API_BASE_URL: process.env.API_BASE_URL || '',
  }),
  docs: {},
  typescript: {
    reactDocgen: 'react-docgen-typescript',
  },
};

export default config;
