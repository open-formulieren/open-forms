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

            component: '',
            formStep: null,
            formStepUuid: null,
            variable: 'bar',
          },
        ],
      },
    ],

    availableFormVariables: AVAILABLE_FORM_VARIABLES,
    availableFormSteps: AVAILABLE_FORM_STEPS,
  },
};
