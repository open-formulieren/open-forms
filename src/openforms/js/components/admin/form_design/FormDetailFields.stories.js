import {fn} from 'storybook/test';

import {FormDecorator} from 'components/admin/form_design/story-decorators';

import FormDetailFields from './FormDetailFields';

export default {
  title: 'Form design / Tabs / Form / Detail fields',
  decorators: [FormDecorator],
  component: FormDetailFields,
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
      submissionAllowed: true,
      suspensionAllowed: true,
      askPrivacyConsent: 'global_setting',
      askStatementOfTruth: 'global_setting',
      appointmentOptions: {
        isAppointment: false,
      },
      translations: {
        nl: {
          name: 'Mijn formulier',
          explanationTemplate: '',
          introductionPageContent: '',
        },
        en: {
          name: 'My form',
          explanationTemplate: '',
          introductionPageContent: '',
        },
      },
    },
    onChange: fn(),
  },
};

export const Default = {};
