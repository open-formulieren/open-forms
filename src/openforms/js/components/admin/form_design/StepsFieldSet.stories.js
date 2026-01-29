import {fn} from 'storybook/test';

import {
  AdminChangeFormDecorator,
  FormDecorator,
} from 'components/admin/form_design/story-decorators';

import {StepsFieldSet} from './form-creation-form';

export default {
  title: 'Form design / Tabs / Steps',
  decorators: [
    FormDecorator,
    Story => (
      <div className="react-form-create">
        <Story />
      </div>
    ),
    AdminChangeFormDecorator,
  ],
  component: StepsFieldSet,
  args: {
    submitting: false,
    loadingErrors: '',
    steps: [
      {
        configuration: {
          display: 'form',
          components: [],
        },
        formDefinition: '',
        index: 0,
        name: 'Step 1',
        internalName: '',
        slug: 'step-1',
        isApplicable: true,
        loginRequired: false,
        isReusable: false,
        url: '',
        isNew: false,
        validationErrors: [],
        translations: {
          nl: {
            name: 'Stap 1',
            saveText: '',
            previousText: '',
            nextText: '',
          },
          en: {
            name: 'Step 1',
            saveText: '',
            previousText: '',
            nextText: '',
          },
        },
      },
    ],
    onEdit: fn(),
    onComponentMutated: fn(),
    onFieldChange: fn(),
    onDelete: fn(),
    onReorder: fn(),
    onReplace: fn(),
    onAdd: fn(),
  },
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
  },
};

export const Default = {};

export const WithValidationErrors = {
  args: {
    steps: [
      {
        configuration: {
          display: 'form',
          components: [],
        },
        formDefinition: '',
        index: 0,
        name: 'Step 1',
        internalName: '',
        slug: 'step-1',
        isApplicable: true,
        loginRequired: false,
        isReusable: false,
        url: '',
        isNew: false,
        validationErrors: [['translations.nl.name', 'Computer says no']],
        translations: {
          nl: {
            name: 'Stap 1',
            saveText: '',
            previousText: '',
            nextText: '',
          },
          en: {
            name: 'Step 1',
            saveText: '',
            previousText: '',
            nextText: '',
          },
        },
      },
    ],
  },
};
