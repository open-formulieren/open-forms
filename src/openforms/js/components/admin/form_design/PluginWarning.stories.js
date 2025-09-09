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
        label: 'Dummy',
        providesAuth: [],
      },
    ],
    selectedAuthPlugins: [],
    availablePrefillPlugins: [
      {
        id: 'dummy-prefill',
        label: 'Dummy',
        requiresAuth: ['bsn'],
        requiresAuthPlugin: [],
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

export const PrefillAuthPluginNotUsed = {
  args: {
    configuration: {
      components: [
        {
          type: 'textfield',
          key: 'someTextField',
          label: 'Some textfield',
          prefill: {
            plugin: 'eidas-citizen',
          },
        },
      ],
    },
    availableAuthPlugins: [
      {
        id: 'eidas_oidc',
        label: 'eIDAS (citizen)',
        providesAuth: ['bsn', 'pseudo'],
      },
      {
        id: 'digid',
        label: 'DigiD',
        providesAuth: ['bsn'],
      },
    ],
    selectedAuthPlugins: ['digid'],
    availablePrefillPlugins: [
      {
        id: 'eidas-citizen',
        requiresAuth: ['bsn', 'pseudo'],
        requiresAuthPlugin: ['eidas_oidc'],
      },
    ],
  },
};
