import {
  FormModalContentDecorator,
  FormikDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import OrgOidcOptionsFormFields from './OrgOidcOptionsFormFields';

const NAME = 'form.authBackends.0.options';

export default {
  title: 'Form design/Authentication/OrgOIDC',
  component: OrgOidcOptionsFormFields,
  decorators: [FormikDecorator, ValidationErrorsDecorator, FormModalContentDecorator],
  args: {
    name: NAME,
    plugin: {
      id: 'org-oidc',
      label: 'Organization via OpenID Connect',
      providesAuth: [],
      schema: {
        type: 'object',
        properties: {
          visible: {
            type: 'boolean',
          },
        },
      },
    },
  },
};

export const Default = {};
