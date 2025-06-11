import {expect, waitFor, within} from '@storybook/test';

import {
  FormModalContentDecorator,
  FormikDecorator,
  ValidationErrorsDecorator,
} from 'components/admin/form_design/story-decorators';
import {rsSelect} from 'utils/storybookTestHelpers';

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
      providesAuth: ['bsn', 'kvk', 'pseudo'],
      schema: {
        type: 'object',
        properties: {
          authenticationOptions: {
            type: 'array',
            items: {
              type: 'string',
              enum: ['bsn', 'kvk'],
              enumNames: ['BSN', 'KvK number'],
            },
            title: 'Authentication options',
            description:
              'Available authentication options that the user can choice from. The user must chose one of the options. If left empty, a hashed value will be used as authentication identifier.',
          },
          additionalAttributesGroups: {
            type: 'array',
            items: {
              type: 'string',
              enum: ['custom_group', 'profile'],
              enumNames: ['A custom group for fetching custom attributes', 'Profile group'],
            },
            title: 'Additional attributes groups',
            description: 'Additional attributes groups to use for authentication.',
          },
          bsnLoa: {
            type: 'string',
            enum: [
              '',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI',
            ],
            enumNames: ['', 'DigiD Basis', 'DigiD Midden', 'DigiD Substantieel', 'DigiD Hoog'],
            title: 'options bsn LoA',
            description: 'The minimal LoA for bsn authentication.',
          },
          kvkLoa: {
            type: 'string',
            enum: [
              '',
              'urn:etoegang:core:assurance-class:loa1',
              'urn:etoegang:core:assurance-class:loa2',
              'urn:etoegang:core:assurance-class:loa2plus',
              'urn:etoegang:core:assurance-class:loa3',
              'urn:etoegang:core:assurance-class:loa4',
            ],
            enumNames: [
              '',
              'Non existent (1)',
              'Low (2)',
              'Low (2+)',
              'Substantial (3)',
              'High (4)',
            ],
            title: 'options kvk LoA',
            description: 'The minimal LoA for kvk authentication.',
          },
        },
      },
    },
  },
};

export const Default = {};

export const DynamicOptionsBasedOnAuthenticationOptions = {
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const authenticationOptionsSelect = canvas.getAllByRole('combobox')[0];
    expect(authenticationOptionsSelect).toHaveValue('');

    await rsSelect(authenticationOptionsSelect, 'BSN');
    const bsnOptionsFieldset = canvas.getByRole('heading', {
      name: 'Yivi plugin options for bsn',
    });
    await waitFor(() => {
      expect(bsnOptionsFieldset).toBeVisible();
    });

    await rsSelect(authenticationOptionsSelect, 'KvK number');
    const kvkOptionsFieldset = canvas.getByRole('heading', {
      name: 'Yivi plugin options for kvk',
    });
    await waitFor(() => {
      expect(kvkOptionsFieldset).toBeVisible();
    });
  },
};
