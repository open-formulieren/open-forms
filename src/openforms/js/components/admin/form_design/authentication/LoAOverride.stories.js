import {expect, within} from '@storybook/test';
import PropTypes from 'prop-types';

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
      schema: {
        type: 'object',
        properties: {
          loa: {
            type: 'string',
            title: 'LoA',
            description: 'LoA options',
            enum: [
              '',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard',
              'urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI',
            ],
            enumNames: ['', 'DigiD Basis', 'DigiD Midden', 'DigiD Substantieel', 'DigiD Hoog'],
          },
        },
      },
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
