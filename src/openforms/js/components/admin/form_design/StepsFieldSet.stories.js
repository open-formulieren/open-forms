import {expect, fn, within} from 'storybook/test';

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

export const RegularFormStepsExample = {
  args: {
    form: {type: 'regular'},
  },
};

export const SingleStepFormStepsExample = {
  args: {
    form: {type: 'single_step'},
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const loginRequired = canvas.queryByText('Vereist authenticatie');
    expect(loginRequired).toBeNull();
  },
};

export const WithValidationErrors = {
  args: {
    form: {type: 'regular'},
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

export const BrokenSimpleLogicReferenceWarnings = {
  args: {
    form: {type: 'regular'},
    steps: [
      {
        configuration: {
          display: 'form',
          components: [
            {
              id: 'component1',
              type: 'textfield',
              key: 'textfield',
              label: 'Text field',
              conditional: {
                show: true,
                when: 'brokenReference',
                eq: 'present',
              },
            },
            {
              id: 'component2',
              type: 'editgrid',
              key: 'editgrid',
              label: 'Repeating group',
              components: [
                {
                  id: 'component3',
                  type: 'checkbox',
                  key: 'trigger',
                  label: 'Trigger',
                },
                {
                  id: 'component4',
                  type: 'number',
                  key: 'number',
                  label: 'Number',
                  conditional: {
                    show: true,
                    when: 'editgrid.trigger',
                    eq: true,
                  },
                },
              ],
            },
          ],
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
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const warnings = canvas.getAllByText(/Component.*steunt op een niet-bestaande component key/);
    expect(warnings).toHaveLength(1);
  },
};
