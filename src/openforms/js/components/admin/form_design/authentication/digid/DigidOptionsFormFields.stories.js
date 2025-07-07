import {
  FormModalContentDecorator,
  FormikDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import DigidOptionsFormFields from './DigidOptionsFormFields';

const NAME = 'form.authBackends.0.options';

export default {
  title: 'Form design/Authentication/DigiD',
  component: DigidOptionsFormFields,
  decorators: [FormikDecorator, ValidationErrorsDecorator, FormModalContentDecorator],
  args: {
    name: NAME,
    plugin: {
      id: 'digid',
      label: 'DigiD',
      providesAuth: ['bsn'],
      schema: {
        type: 'object',
        properties: {
          loa: {
            type: 'string',
            enum: [
              '',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI',
            ],
            enumNames: ['', 'DigiD Basis', 'DigiD Midden', 'DigiD Substantieel', 'DigiD Hoog'],
            title: 'options LoA',
            description: 'The minimal LoA for authentication.',
          },
        },
        required: ['loa'],
      },
    },
  },
};

export const Default = {};
