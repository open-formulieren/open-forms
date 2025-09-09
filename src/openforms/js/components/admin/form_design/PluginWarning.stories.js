import {FormDecorator} from 'components/admin/form_design/story-decorators';

import PluginWarning from './PluginWarning';

export default {
  title: 'Form Design / Form Step / PluginWarning',
  component: PluginWarning,
  decorators: [FormDecorator],
  args: {
    loginRequired: false,
    configuration: {
      components: [
        {
          type: 'textfield',
          key: 'someTextField',
          label: 'Some textfield',
        },
      ],
    },
    availableAuthPlugins: [
      {
        id: 'dummy-auth',
        providesAuth: [],
      },
    ],
    selectedAuthPlugins: [],
    availablePrefillPlugins: [
      {
        id: 'dummy-prefill',
        requiresAuth: ['bsn'],
      },
    ],
  },
};

export const NoWarnings = {};

export const LoginRequiredWithoutAuthPlugin = {
  args: {
    loginRequired: true,
  },
};

export const PrefillAuthAttributeNotProvided = {
  args: {
    configuration: {
      components: [
        {
          type: 'textfield',
          key: 'someTextField',
          label: 'Some textfield',
          prefill: {
            plugin: 'dummy-prefill',
          },
        },
      ],
    },
  },
};
