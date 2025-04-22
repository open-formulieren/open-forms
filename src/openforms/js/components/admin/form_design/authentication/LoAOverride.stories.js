import {expect, within} from '@storybook/test';

import {AdminChangeFormDecorator} from 'components/admin/form_design/story-decorators';

import LoAOverride from './LoAOverride';

export default {
  title: 'Form design/ Authentication / LoA override',
  component: LoAOverride,
  decorators: [AdminChangeFormDecorator],
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
  },
};

export const Default = {
  args: {
    plugin: {
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
    loa: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldLabel = canvas.queryByText('Minimale betrouwbaarheidsniveaus');

    expect(fieldLabel).toBeVisible();

    const dropdowns = canvas.getAllByRole('combobox');

    expect(dropdowns.length).toEqual(1);
  },
};
