import {
  FormModalContentDecorator,
  FormikDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';

import YiviOptionsFormFields from './YiviOptionsFormFields';

const NAME = 'form.authBackends.0.options';

export default {
  title: 'Form design/Authentication/Yivi',
  component: YiviOptionsFormFields,
  decorators: [FormikDecorator, ValidationErrorsDecorator, FormModalContentDecorator],
  args: {
    name: NAME,
    plugin: {
      id: 'yivi_oidc',
      label: 'Yivi via OpenID Connect',
      providesAuth: 'bsn',
      schema: {
        type: 'object',
        properties: {
          authenticationAttribute: {
            type: 'string',
            enum: ['bsn', 'kvk', 'pseudo'],
            enumNames: ['BSN', 'KvK number', 'Pseudo ID'],
            title: 'Authentication attribute',
            description: 'The authentication attribute that will be fetched.',
          },
          additionalScopes: {
            type: 'array',
            items: {
              type: 'string',
              enum: ['custom_scope'],
              enumNames: ['Een custom scope voor het ophalen van custom claims'],
            },
            title: 'Additional scopes',
            description: 'Additional scopes to use for authentication.',
          },
        },
        required: ['authenticationAttribute'],
        discriminator: {
          propertyName: 'authentication_attribute',
          mappings: {
            bsn: {
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
                  enumNames: [
                    '',
                    'DigiD Basis',
                    'DigiD Midden',
                    'DigiD Substantieel',
                    'DigiD Hoog',
                  ],
                  title: 'options LoA',
                  description: 'The minimal LoA for authentication.',
                },
              },
            },
            kvk: {
              type: 'object',
              properties: {},
            },
            pseudo: {
              type: 'object',
              properties: {},
            },
          },
        },
        anyOf: [
          {
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
          },
          {
            type: 'object',
            properties: {},
          },
          {
            type: 'object',
            properties: {},
          },
        ],
      },
    },
  },
};

export const Default = {};
