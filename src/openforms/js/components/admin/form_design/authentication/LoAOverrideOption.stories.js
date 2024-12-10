import {expect, within} from '@storybook/test';

import {AdminChangeFormDecorator} from 'components/admin/form_design/story-decorators';

import LoAOverrideOption from './LoAOverrideOption';

export default {
  title: 'Form design/ Authentication / LoA override option',
  component: LoAOverrideOption,
  decorators: [AdminChangeFormDecorator],
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
  },
};

export const Default = {
  args: {
    availableAuthPlugins: [
      {
        id: 'digid',
        label: 'DigiD',
        providesAuth: 'bsn',
        supportsLoaOverride: true,
        assuranceLevels: [
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
            label: 'DigiD Basis',
          },
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract',
            label: 'DigiD Midden',
          },
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard',
            label: 'DigiD Substantieel',
          },
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI',
            label: 'DigiD Hoog',
          },
        ],
      },
      {
        id: 'eidas',
        label: 'eIDAS',
        providesAuth: 'pseudo',
        supportsLoaOverride: false,
        assuranceLevels: [],
      },
    ],
    selectedAuthPlugins: ['digid', 'eidas'],
    authenticationBackendOptions: {
      digid: {loa: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport'},
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldLabel = canvas.queryByText('Minimale betrouwbaarheidsniveaus');

    await expect(fieldLabel).toBeVisible();

    const dropdowns = canvas.getAllByRole('combobox');

    await expect(dropdowns.length).toEqual(1);
  },
};

export const NoDigiDSelected = {
  name: 'No DigiD selceted',
  args: {
    availableAuthPlugins: [
      {
        id: 'digid',
        label: 'DigiD',
        providesAuth: 'bsn',
        supportsLoaOverride: true,
        assuranceLevels: [
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
            label: 'DigiD Basis',
          },
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract',
            label: 'DigiD Midden',
          },
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard',
            label: 'DigiD Substantieel',
          },
          {
            value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI',
            label: 'DigiD Hoog',
          },
        ],
      },
      {
        id: 'eidas',
        label: 'eIDAS',
        providesAuth: 'pseudo',
        supportsLoaOverride: false,
        assuranceLevels: [],
      },
    ],
    selectedAuthPlugins: ['eidas'],
    authenticationBackendOptions: {
      digid: {loa: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport'},
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldLabel = canvas.queryByText('Minimale betrouwbaarheidsniveaus');

    await expect(fieldLabel).toBeNull();

    const dropdowns = canvas.queryAllByRole('combobox');

    await expect(dropdowns.length).toEqual(0);
  },
};
