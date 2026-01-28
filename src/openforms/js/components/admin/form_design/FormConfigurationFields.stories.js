import {expect, fn, userEvent, within} from 'storybook/test';

import FormConfigurationFields from './FormConfigurationFields';

export default {
  title: 'Form design / Tabs / Form / Configuration fields',
  component: FormConfigurationFields,
  args: {
    form: {
      uuid: '',
      internalName: '',
      slug: 'my-form',
      showProgressIndicator: true,
      showSummaryProgress: false,
      active: true,
      category: '',
      theme: '',
      isDeleted: false,
      activateOn: null,
      deactivateOn: null,
      maintenanceMode: false,
      translationEnabled: false,
      submissionAllowed: 'yes',
      suspensionAllowed: true,
      askPrivacyConsent: 'global_setting',
      askStatementOfTruth: 'global_setting',
      appointmentOptions: {
        isAppointment: false,
      },
      authBackends: [],
    },
    onChange: fn(),
    availableAuthPlugins: [
      {
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
              title: 'options bsn LoA',
              description: 'The minimal LoA for bsn authentication.',
            },
          },
        },
      },
      {
        id: 'eherkenning',
        label: 'eHerkenning',
        providesAuth: ['kvk'],
      },
    ],
    availableThemes: [
      {
        url: '/api/v2/themes/1',
        name: 'Open Forms',
      },
    ],
    selectedAuthPlugins: [],
    onAuthPluginChange: fn(),
    availableCategories: [
      {
        name: 'Parent',
        url: '/apiv/2/categories/1',
        ancestors: [],
      },
      {
        name: 'Child',
        url: '/apiv/2/categories/2',
        ancestors: [{name: 'Parent'}],
      },
      {
        name: 'Category 3',
        url: '/apiv/2/categories/3',
        ancestors: [],
      },
    ],
  },
};

export const Default = {};

export const AuthenticationPluginWithOptionsModal = {
  args: {
    form: {
      authBackends: [
        {
          backend: 'digid',
          options: {
            loa: '',
          },
        },
      ],
    },
    selectedAuthPlugins: ['digid'],
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const authTitle = canvas.getByRole('heading', {name: 'Inloggen (Tonen)'});
    expect(authTitle).toBeVisible();
    await userEvent.click(within(authTitle).getByRole('link', {name: '(Tonen)'}));

    await userEvent.click(canvas.getByRole('button', {name: 'Opties instellen'}));

    expect(canvas.getByRole('heading', {name: 'Plugin-instellingen: DigiD'})).toBeVisible();
  },
};
