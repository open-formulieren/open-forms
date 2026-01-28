import {expect, within} from 'storybook/test';

import {
  AdminChangeFormDecorator,
  FormikDecorator,
} from 'components/admin/form_design/story-decorators';

import LoAOverride from './LoAOverride';

export default {
  title: 'Form design/ Authentication / LoA override',
  component: LoAOverride,
  decorators: [FormikDecorator, AdminChangeFormDecorator],
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
    formik: {
      initialValues: {
        loa: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
      },
    },
  },
};

export const Default = {
  args: {
    name: 'loa',
    options: [
      {
        label: '---',
        value: '',
      },
      {
        label: 'DigiD Basis',
        value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport',
      },
      {
        label: 'DigiD Midden',
        value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract',
      },
      {
        label: 'DigiD Substantieel',
        value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:Smartcard',
      },
      {
        label: 'DigiD Hoog',
        value: 'urn:oasis:names:tc:SAML:2.0:ac:classes:SmartcardPKI',
      },
    ],
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const fieldLabel = canvas.queryByText('Minimale betrouwbaarheidsniveaus');

    expect(fieldLabel).toBeVisible();

    const dropdowns = canvas.getAllByRole('combobox');

    expect(dropdowns.length).toEqual(1);
  },
};
