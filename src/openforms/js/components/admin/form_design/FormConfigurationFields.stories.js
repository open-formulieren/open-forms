import {fn} from '@storybook/test';

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
      authenticationBackendOptions: {},
    },
    onChange: fn(),
    availableAuthPlugins: [
      {
        id: 'digid',
        label: 'DigiD',
        providesAuth: 'bsn',
      },
      {
        id: 'eherkenning',
        label: 'eHerkenning',
        providesAuth: 'kvk',
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
