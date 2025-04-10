import {FormDecorator} from 'components/admin/form_design/story-decorators';

import OIDCPluginScopesConfiguration from './OIDCPluginScopesConfiguration';

export default {
  title: 'Form design/ Authentication / OIDC plugin scopes configuration',
  component: OIDCPluginScopesConfiguration,
  decorators: [FormDecorator],

  args: {
    prefix: '',
    onChange: () => {},
    authenticationOidcPluginScopes: [
      {
        pluginId: 'digid_oidc',
        scopes: ['address'],
      },
    ],
    availableAuthPlugins: [
      {
        id: 'digid_oidc',
        label: 'DigiD via OIDC',
        providesAuth: 'bsn',
      },
    ],
  },
  argTypes: {},
};

export const Default = {};
