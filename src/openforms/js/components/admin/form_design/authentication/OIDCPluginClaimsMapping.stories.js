import {FormDecorator} from 'components/admin/form_design/story-decorators';

import {VARIABLE_SOURCES} from '../variables/constants';
import OIDCPluginClaimsMapping from './OIDCPluginClaimsMapping';

export default {
  title: 'Form design/ Authentication / OIDC plugin claims mapping',
  component: OIDCPluginClaimsMapping,
  decorators: [FormDecorator],

  args: {
    prefix: '',
    onChange: () => {},
    pluginClaims: {
      pluginId: 'digid_oidc',
      claimMapping: [{claimName: 'first_name', formVariable: 'key2'}],
    },
    availableFormVariables: [
      {
        form: 'bar',
        formDefinition: 'bar',
        name: 'First name',
        key: 'key2',
        source: VARIABLE_SOURCES.component,
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
