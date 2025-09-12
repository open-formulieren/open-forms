import {useArgs} from '@storybook/preview-api';
import {expect, userEvent, waitFor, within} from '@storybook/test';
import {produce} from 'immer';
import set from 'lodash/set';

import {
  mockDMNDecisionDefinitionVersionsGet,
  mockDMNDecisionDefinitionsGet,
} from 'components/admin/form_design/mocks';
import {FormDecorator, FormLogicDecorator} from 'components/admin/form_design/story-decorators';

import Action from './Action';

export default {
  title: 'Form design/FormLogic/Action',
  decorators: [FormDecorator, FormLogicDecorator],
  component: Action,
  argTypes: {},
};

const AVAILABLE_SERVICES = [
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
];

const SERVICE_FETCH_CONFIGURATIONS = [
  {
    name: 'Foo fetch',
    id: 1,
    service: 'http://foo.com/services/1',
    path: '/some-path',
    method: 'GET',
    headers: [['X-Foo', 'foo']],
    queryParams: [['parameter2', ['value1', 'value2']]],
    body: {field1: 'value', field2: 'value2'},
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
    body: {field1: 'value', field2: 'value2'},
    dataMappingType: 'JsonLogic',
    mappingExpression: {var: 'field'},
  },
];

const render = ({prefixText, errors, onDelete}) => {
  const [{action}, updateArgs] = useArgs();
  const onChange = event => {
    const {name, value} = event.target;
    const newAction = produce(action, draft => {
      set(draft, name, value);
    });
    updateArgs({action: newAction});
  };
  return (
    <Action
      prefixText={prefixText}
      action={action}
      errors={errors}
      onChange={onChange}
      onDelete={onDelete}
    />
  );
};

export const ServiceFetch = {
  render,
  name: 'Service fetch',

  args: {
    prefixText: 'Action',

    action: {
      component: '',
      variable: 'bar',
      formStep: '',
      formStepUuid: '',

      action: {
        type: 'fetch-from-service',
        value: '',
      },
    },

    errors: {},
    availableServices: AVAILABLE_SERVICES,
    serviceFetchConfigurations: SERVICE_FETCH_CONFIGURATIONS,

    availableFormSteps: [
      {
        formDefinition:
          'http://localhost:8000/api/v2/form-definitions/b4de3050-3d55-4d7e-bdec-c4ec2ff330f8',

        configuration: {
          display: 'form',
        },

        slug: 'step-1',
        name: 'Step 1',
        url: 'http://localhost:8000/api/v2/forms/42bda734-de31-4f0a-87c9-bf36085ffc75/steps/8f046d57-ef41-41e0-bb7a-a8dc618b9d43',
        uuid: '8f046d57-ef41-41e0-bb7a-a8dc618b9d43',
        _generatedId: '',
        isNew: false,
        validationErrors: [],
      },
    ],

    availableStaticVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/42bda734-de31-4f0a-87c9-bf36085ffc75',
        formDefinition: '',
        name: 'Foo',
        key: 'foo',
      },
    ],

    availableFormVariables: [
      {
        form: 'http://localhost:8000/api/v2/forms/42bda734-de31-4f0a-87c9-bf36085ffc75',
        formDefinition:
          'http://localhost:8000/api/v2/form-definitions/b4de3050-3d55-4d7e-bdec-c4ec2ff330f8',
        name: 'Bar',
        key: 'bar',
      },
    ],
  },
};

export const EvaluateDMN = {
  render,
  name: 'Evaluate DMN',
  args: {
    prefixText: 'Action',

    action: {
      component: '',
      variable: 'bar',
      formStep: '',
      formStepUuid: '',

      action: {
        config: {},
        type: 'evaluate-dmn',
        value: '',
      },
    },
    availableDMNPlugins: [
      {id: 'camunda7', label: 'Camunda 7'},
      {id: 'some-other-engine', label: 'Some other engine'},
    ],
    availableFormVariables: [
      {type: 'textfield', key: 'name', name: 'Name'},
      {type: 'textfield', key: 'surname', name: 'Surname'},
      {type: 'number', key: 'income', name: 'Income'},
      {type: 'checkbox', key: 'canApply', name: 'Can apply?'},
    ],
  },
  decorators: [FormDecorator],

  parameters: {
    msw: {
      handlers: [
        mockDMNDecisionDefinitionsGet({
          camunda7: [
            {
              id: 'approve-payment',
              label: 'Approve payment',
            },
            {
              id: 'invoiceClassification',
              label: 'Invoice Classification',
            },
          ],
          'some-other-engine': [{id: 'some-definition-id', label: 'Some definition id'}],
        }),
        mockDMNDecisionDefinitionVersionsGet,
      ],
    },
  },
};

export const EvaluateDMNWithInitialErrors = {
  render,
  name: 'Evaluate DMN with initial errors',
  args: {
    prefixText: 'Action',

    action: {
      component: '',
      variable: 'bar',
      formStep: '',
      formStepUuid: '',

      action: {
        config: {
          pluginId: '',
          decisionDefinitionId: '',
        },
        type: 'evaluate-dmn',
        value: '',
      },
    },
    errors: {
      action: {
        config: {
          pluginId: 'This field is required.',
          decisionDefinitionId: 'This field is required.',
        },
      },
    },
    availableDMNPlugins: [
      {id: 'camunda7', label: 'Camunda 7'},
      {id: 'some-other-engine', label: 'Some other engine'},
    ],
    availableFormVariables: [
      {type: 'textfield', key: 'name', name: 'Name'},
      {type: 'textfield', key: 'surname', name: 'Surname'},
      {type: 'number', key: 'income', name: 'Income'},
      {type: 'checkbox', key: 'canApply', name: 'Can apply?'},
    ],
  },
  decorators: [FormDecorator],

  parameters: {
    msw: {
      handlers: [
        mockDMNDecisionDefinitionsGet({
          camunda7: [
            {
              id: 'approve-payment',
              label: 'Approve payment',
            },
            {
              id: 'invoiceClassification',
              label: 'Invoice Classification',
            },
          ],
          'some-other-engine': [{id: 'some-definition-id', label: 'Some definition id'}],
        }),
        mockDMNDecisionDefinitionVersionsGet,
      ],
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    step('Verify that global DMN config error is shown', () => {
      expect(
        canvas.getByRole('listitem', {text: 'De DMN-instellingen zijn niet geldig.'})
      ).toBeVisible();
    });

    step('Open configuration modal', async () => {
      await userEvent.click(canvas.getByRole('button', {name: 'Instellen'}));

      const dialog = within(canvas.getByRole('dialog'));

      const pluginDropdown = dialog.getByLabelText('Plugin');
      const decisionDefDropdown = dialog.getByLabelText('Beslisdefinitie-ID');

      // Mark dropdowns as touched
      await userEvent.click(pluginDropdown);
      await userEvent.click(decisionDefDropdown);
      await userEvent.tab();

      await waitFor(async () => {
        const errorMessages = dialog.getAllByRole('listitem');

        expect(errorMessages.length).toBe(2);
      });
    });
  },
};

export const SynchronizeVariables = {
  render,
  name: 'Synchronize children',
  args: {
    prefixText: 'Action',

    action: {
      component: '',
      variable: '',
      formStep: '',
      formStepUuid: '',

      action: {
        config: {},
        type: 'synchronize-variables',
        value: '',
      },
    },
    availableComponents: {
      children: {
        key: 'children',
        type: 'children',
        label: 'Children',
      },
      editgrid: {
        key: 'editgrid',
        type: 'editgrid',
        label: 'Editgrid',
        components: [
          {
            key: 'bsn',
            type: 'bsn',
            label: 'BSN',
          },
          {
            key: 'firstNames',
            type: 'textfield',
            label: 'First names',
          },
        ],
      },
      'editgrid.bsn': {
        key: 'bsn',
        type: 'bsn',
        label: 'BSN',
      },
      'editgrid.firstNames': {
        key: 'firstNames',
        type: 'textfield',
        label: 'First names',
      },
    },
    availableFormVariables: [
      {
        dataFormat: '',
        dataType: 'array',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'children',
        name: 'children',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
      {
        dataFormat: '',
        dataType: 'array',
        form: 'http://localhost:8000/api/v2/forms/ae26e20c-f059-4fdf-bb82-afc377869bb5',
        formDefinition: null,
        initialValue: '',
        isSensitiveData: false,
        key: 'editgrid',
        name: 'editgrid',
        prefillAttribute: '',
        prefillPlugin: '',
        source: 'component',
      },
    ],
  },
  decorators: [FormDecorator],
};
