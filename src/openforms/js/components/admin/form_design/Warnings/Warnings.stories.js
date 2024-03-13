import {FormDecorator} from 'components/admin/form_design/story-decorators';

import {FormWarnings, MissingAuthCosignWarning as MissingAuthCosignWarningComponent} from '.';

export default {
  title: 'Form design/FormWarnings',
  component: FormWarnings,
  decorators: [FormDecorator],
};

export const FormWarningsWithoutTranslations = {
  name: 'Form Warnings - translations not enabled',
  args: {
    form: {
      translationEnabled: false,
      translations: {en: {}, nl: {}},
      confirmationEmailTemplate: 'This is a confirmation email template.',
    },
    availableFormSteps: [
      {
        uuid: '21f8bb15-f660-4e4c-ae9d-ba80e23161d1',
        index: 0,
        slug: 'cosign-step',
        configuration: {
          display: 'form',
          components: [
            {
              key: 'mainPersonEmail',
              type: 'email',
              label: 'Main person email',
            },
            {
              key: 'coSignerEmail',
              type: 'cosign',
              label: 'Co-signer email',
            },
            {
              type: 'editgrid',
              key: 'repeatingGroup',
              components: [
                {
                  key: 'extraCoSignerEmail',
                  type: 'cosign',
                  label: 'Extra co-signer email',
                },
              ],
            },
          ],
        },
        formDefinition:
          'http://test-of.nl/api/v2/form-definitions/d208cd64-2c5b-4a45-9919-7af5de853906',
        name: 'Co-sign step',
        url: 'http://test-of.nl/api/v2/forms/a7882c37-846e-4389-b0f4-c2d7c040093f/steps/21f8bb15-f660-4e4c-ae9d-ba80e23161d1',
        loginRequired: true,
        isReusable: false,
        literals: {
          previousText: {
            resolved: 'Previous page',
            value: '',
          },
          saveText: {
            resolved: 'Save current information',
            value: '',
          },
          nextText: {
            resolved: 'Next',
            value: '',
          },
        },
        translations: {
          nl: {
            previousText: '',
            saveText: '',
            nextText: '',
            name: 'Co-sign step',
          },
          en: {
            previousText: '',
            saveText: '',
            nextText: '',
            name: '',
          },
        },
        validationErrors: [],
      },
    ],
    availableComponents: {
      mainPersonEmail: {
        key: 'mainPersonEmail',
        type: 'email',
        label: 'Main person email',
      },
      coSignerEmail: {
        key: 'coSignerEmail',
        type: 'cosign',
        label: 'Co-signer email',
        authPlugin: 'digid',
      },
      repeatingGroup: {
        type: 'editgrid',
        key: 'repeatingGroup',
        components: [
          {
            key: 'extraCoSignerEmail',
            type: 'cosign',
            label: 'Co-signer email',
          },
        ],
      },
      'repeatingGroup.extraCoSignerEmail': {
        key: 'extraCoSignerEmail',
        type: 'cosign',
        label: 'Co-signer email',
      },
    },
    availableAuthPlugins: [
      {
        id: 'digid',
        label: 'DigiD',
        providesAuth: ['bsn'],
      },
      {
        id: 'demo',
        label: 'Demo DigiD',
        providesAuth: ['bsn'],
      },
    ],
    selectedAuthPlugins: [],
  },
};

export const MissingAuthCosignWarning = {
  name: 'Warning missing authentication plugin for co-sign component',
  component: MissingAuthCosignWarningComponent,
  args: {
    form: {
      selectedAuthPlugins: [],
    },
    availableComponents: {
      mainPersonEmail: {
        key: 'mainPersonEmail',
        type: 'email',
        label: 'Main person email',
      },
      coSignerEmail: {
        key: 'coSignerEmail',
        type: 'cosign',
        label: 'Co-signer email',
        authPlugin: 'digid',
      },
    },
    availableAuthPlugins: [
      {
        id: 'digid',
        label: 'DigiD',
        providesAuth: ['bsn'],
      },
    ],
  },
};
