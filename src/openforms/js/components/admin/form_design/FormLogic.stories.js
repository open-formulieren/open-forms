import {expect, fn, userEvent, waitFor, within} from 'storybook/test';

import {
  FeatureFlagsDecorator,
  FormDecorator,
  FormLogicDecorator,
} from 'components/admin/form_design/story-decorators';

import {FormLogic} from './FormLogic';
import {mockServiceFetchConfigurationsGet, mockServicesGet} from './mocks';

const AVAILABLE_FORM_VARIABLES = [
  {
    dataFormat: '',
    dataType: 'string',
    form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
    formDefinition: null,
    initialValue: true,
    isSensitiveData: false,
    key: 'foo',
    name: 'Foo',
    prefillAttribute: '',
    prefillPlugin: '',
    source: 'user_defined',
  },
  {
    dataFormat: '',
    dataType: 'boolean',
    form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
    formDefinition: null,
    initialValue: true,
    isSensitiveData: false,
    key: 'bar',
    name: 'Bar',
    prefillAttribute: '',
    prefillPlugin: '',
    source: 'user_defined',
  },
];

const AVAILABLE_FORM_STEPS = [
  {
    formDefinition:
      'http://localhost:8000/api/v2/form-definitions/b4de3050-3d55-4d7e-bdec-c4ec2ff330f8',
    configuration: {display: 'form'},
    slug: 'step-1',
    name: 'Step 1',
    url: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5/steps/8f046d57-ef41-41e0-bb7a-a8dc618b9d43',
    uuid: '8f046d57-ef41-41e0-bb7a-a8dc618b9d43',
    _generatedId: '',
    isNew: false,
    validationErrors: [],
  },
];

export default {
  title: 'Form design/FormLogic',
  component: FormLogic,
  decorators: [FeatureFlagsDecorator, FormDecorator, FormLogicDecorator],

  args: {
    onChange: fn(),
    onServiceFetchAdd: fn(),
    onDelete: fn(),
    onAdd: fn(),
  },

  parameters: {
    msw: {
      handlers: [
        mockServicesGet([
          {
            url: 'http://foo.com/services/1',
            label: 'Service 1',
            apiRoot: 'http://foo.com/api/v1/',
            apiType: 'ORC',
          },
          {
            url: 'http://foo.com/services/2',
            label: 'Service 2',
            apiRoot: 'http://bar.com/api/v1/',
            apiType: 'ORC',
          },
        ]),
        mockServiceFetchConfigurationsGet([
          {
            name: 'Foo fetch',
            id: 1,
            service: 'http://foo.com/services/1',
            path: '/some-path',
            method: 'GET',
            headers: [['X-Foo', 'foo']],
            queryParams: [['parameter2', ['value1', 'value2']]],

            body: {
              field1: 'value',
              field2: 'value2',
            },

            dataMappingType: 'jq',
            mappingExpression: '.field.nested',
          },
          {
            name: '', // No name supplied, should fall back to "method path (service)"
            id: 2,
            service: 'http://foo.com/services/2',
            path: '/some-other-path',
            method: 'POST',
            headers: [['X-Foo', 'bar']],
            queryParams: [
              ['parameter', ['value']],
              ['parameter2', ['value1', 'value2']],
            ],

            body: {
              field1: 'value',
              field2: 'value2',
            },

            dataMappingType: 'JsonLogic',

            mappingExpression: {
              var: 'field',
            },
          },
        ]),
      ],
    },
  },
};

export const FullFunctionality = {
  name: 'Full functionality',

  args: {
    logicRules: [
      {
        uuid: 'foo',
        _generatedId: 'foo', // consumers should generate this, as it's used for the React key prop if no uuid exists
        _logicType: 'simple',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        description: 'Sample rule',
        _mayGenerateDescription: false,
        order: 1,

        jsonLogicTrigger: {
          '==': [
            {
              var: 'foo',
            },
            'bar',
          ],
        },

        isAdvanced: false,

        actions: [
          {
            action: {
              type: 'fetch-from-service',
              value: '',
            },

            uuid: '',
            _generatedId: '0',
            component: '',
            formStepUuid: null,
            variable: 'bar',
          },
        ],
      },
      {
        uuid: 'bar',
        _generatedId: 'bar',
        _logicType: 'advanced',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        description: 'DMN: missing form variable reference',
        _mayGenerateDescription: false,
        order: 1,
        jsonLogicTrigger: true,

        isAdvanced: true,

        actions: [
          {
            action: {
              type: 'evaluate-dmn',
              config: {
                // clicking "Instellen" is known to crash, no mocks are set up to keep
                // the stories simple
                pluginId: 'camunda7',
                decisionDefinitionId: 'decision1',
                decisionDefinitionVersion: '',
                inputMapping: [
                  // empty form var, triggers a warning
                  {formVariable: '', dmnVariable: 'someInput'},
                ],
                outputMapping: [],
              },
            },

            uuid: '',
            _generatedId: '0',
            component: '',
            formStepUuid: null,
            variable: '',
          },
        ],
      },
    ],

    availableFormVariables: AVAILABLE_FORM_VARIABLES,
    availableFormSteps: AVAILABLE_FORM_STEPS,
  },
};

export const DeletingOneOfMultipleActionsInSameTrigger = {
  name: 'Deleting one of multiple actions in the same trigger',

  args: {
    logicRules: [
      {
        uuid: 'foo',
        _generatedId: 'foo', // consumers should generate this, as it's used for the React key prop if no uuid exists
        _logicType: 'simple',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        description: 'Sample rule',
        _mayGenerateDescription: false,
        order: 1,

        jsonLogicTrigger: {
          '==': [
            {
              var: 'foo',
            },
            'bar',
          ],
        },

        isAdvanced: false,

        actions: [
          {
            uuid: '',
            _generatedId: '0',
            component: '',
            variable: 'foo',
            formStepUuid: null,
            action: {
              type: 'variable',
              value: 'First action',
            },
          },
          {
            uuid: '',
            _generatedId: '1',
            component: '',
            variable: 'bar',
            formStepUuid: null,
            action: {
              type: 'variable',
              value: 'Second action',
            },
          },
        ],
      },
    ],

    availableFormVariables: AVAILABLE_FORM_VARIABLES,
    availableFormSteps: AVAILABLE_FORM_STEPS,
  },

  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    // Both actions should be present
    expect(
      await canvas.findByText(/First action/, undefined, {timeout: 10 * 1000})
    ).toBeInTheDocument();
    expect(await canvas.findByText(/Second action/)).toBeInTheDocument();

    // Delete the first action
    const deleteIcons = await canvas.findAllByTitle('Verwijderen');
    expect(deleteIcons).toHaveLength(3);
    await userEvent.click(deleteIcons[1]); // deleteIcons[0] is the delete icon for the entire rule
    await userEvent.click(await canvas.findByRole('button', {name: 'Accepteren'}));

    // First action should be removed, and the second should still be present
    await waitFor(
      () => {
        expect(canvas.queryByText(/First action/)).not.toBeInTheDocument();
        expect(canvas.getByText(/Second action/)).toBeInTheDocument();
      },
      {timeout: 10 * 1000}
    );
  },
};
