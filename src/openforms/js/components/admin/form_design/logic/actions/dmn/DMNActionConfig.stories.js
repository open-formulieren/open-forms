import {expect, fireEvent, userEvent, waitFor, within} from '@storybook/test';

import {
  mockDMNDecisionDefinitionVersionsGet,
  mockDMNDecisionDefinitionsGet,
  mockDMNParametersGet,
} from 'components/admin/form_design/mocks';
import {FormDecorator} from 'components/admin/form_design/story-decorators';

import DMNActionConfig from './DMNActionConfig';

export default {
  title: 'Form design/FormLogic/DMN Action configuration',
  component: DMNActionConfig,
  decorators: [FormDecorator],
  argTypes: {},
  args: {
    availableDMNPlugins: [
      {id: 'camunda7', label: 'Camunda 7'},
      {id: 'some-other-engine', label: 'Some other engine'},
    ],
    availableFormVariables: [
      {type: 'textfield', key: 'name', name: 'Name'},
      {type: 'textfield', key: 'surname', name: 'Surname'},
      {type: 'number', key: 'income', name: 'Income'},
      {type: 'checkbox', key: 'canApply', name: 'Can apply?'},
      {type: 'postcode', key: 'postcode', name: 'Postcode'},
    ],
  },
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
            {
              id: 'withComplexExpressions',
              label: 'Complex expression in inputs',
            },
          ],
          'some-other-engine': [{id: 'some-definition-id', label: 'Some definition id'}],
        }),
        mockDMNDecisionDefinitionVersionsGet,
        mockDMNParametersGet({
          'some-definition-id': {
            inputs: [],
            outputs: [],
          },
          'approve-payment': {
            inputs: [
              {
                label: 'Direction',
                id: 'Input_1',
                typeRef: 'string',
                expression: 'direction',
              },
              {
                label: 'Port number',
                id: 'InputClause_1cn8gp3',
                typeRef: 'integer',
                expression: 'port',
              },
              {
                label: 'Camunda variable',
                id: 'InputClause_1f09wt8',
                typeRef: 'string',
                expression: 'camundaVar',
              },
            ],
            outputs: [
              {
                id: 'Output_1',
                label: 'Policy',
                typeRef: 'string',
                name: 'policy',
              },
              {
                id: 'OutputClause_0lzmnio',
                label: 'Reason',
                typeRef: 'string',
                name: 'reason',
              },
            ],
          },
          invoiceClassification: {
            inputs: [
              {
                id: 'clause1',
                label: 'Invoice Amount',
                expression: 'amount',
                typeRef: 'double',
              },
              {
                id: 'InputClause_15qmk0v',
                label: 'Invoice Category',
                expression: 'invoiceCategory',
                typeRef: 'string',
              },
            ],
            outputs: [
              {
                id: 'clause3',
                label: 'Classification',
                name: 'invoiceClassification',
                typeRef: 'string',
              },
              {
                id: 'OutputClause_1cthd0w',
                label: 'Approver Group',
                name: 'result',
                typeRef: 'string',
              },
            ],
          },
          withComplexExpressions: {
            inputs: [
              {
                label: 'Simple variable',
                id: '',
                typeRef: 'string',
                expression: 'foo',
              },
              {
                label: 'Sum of a and b',
                id: '',
                typeRef: 'integer',
                expression: 'a + b',
              },
              {
                label: 'Numeric part postcode',
                id: '',
                typeRef: 'integer',
                expression: 'number(substring(postcode, 1, 4))',
              },
              {
                label: 'Weird but valid syntax',
                id: '',
                typeRef: 'integer',
                expression: 'a+b',
              },
            ],
            outputs: [
              {
                id: 'OutputClause_1cthd0w',
                label: 'Sole output',
                typeRef: 'string',
                name: 'result',
              },
            ],
          },
        }),
      ],
    },
  },
};

export const Default = {
  args: {
    initialValues: {
      pluginId: '',
      decisionDefinitionId: '',
      decisionDefinitionVersion: '',
      inputMapping: [],
      outputMapping: [],
    },
  },
};

export const Empty = {
  args: {
    initialValues: {
      pluginId: '',
      decisionDefinitionId: '',
      decisionDefinitionVersion: '',
      inputMapping: [],
      outputMapping: [],
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);
    const originalConfirm = window.confirm;
    window.confirm = () => true;

    const pluginDropdown = canvas.getByLabelText('Plugin');
    const decisionDefDropdown = canvas.getByLabelText('Beslisdefinitie-ID');
    const decisionDefVersionDropdown = canvas.getByLabelText('Beslisdefinitieversie');

    await step('Selecting plugin, decision definition and version.', async () => {
      await userEvent.selectOptions(pluginDropdown, 'Camunda 7');

      await expect(pluginDropdown.value).toBe('camunda7');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefDropdown).getAllByRole('option');

        await expect(renderedOptions.length).toBe(4);
      });

      await userEvent.selectOptions(decisionDefDropdown, 'Approve payment');

      await expect(decisionDefDropdown.value).toBe('approve-payment');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefVersionDropdown).getAllByRole('option');

        await expect(renderedOptions.length).toBe(3);
      });

      await userEvent.selectOptions(decisionDefVersionDropdown, 'v2 (version tag: n/a)');

      await expect(decisionDefVersionDropdown.value).toBe('2');
    });

    await step('Adding input mappings', async () => {
      const buttons = canvas.getAllByRole('button');

      await userEvent.click(buttons[0]);

      const dropdowns = within(document.querySelector('.logic-dmn__mapping-config')).getAllByRole(
        'combobox'
      );

      await expect(dropdowns.length).toBe(2);

      const [formVarsDropdowns, dmnVarsDropdown] = dropdowns;

      await userEvent.selectOptions(formVarsDropdowns, 'Name (name)');
      await userEvent.selectOptions(dmnVarsDropdown, 'camundaVar');

      await expect(formVarsDropdowns.value).toBe('name');
      await expect(dmnVarsDropdown.value).toBe('camundaVar');
    });

    await step('Changing plugin clears decision definition, version and DMN vars', async () => {
      await userEvent.selectOptions(pluginDropdown, 'Some other engine');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefDropdown).getAllByRole('option');
        const [formVarsDropdowns, dmnVarsDropdown] = within(
          document.querySelector('.logic-dmn__mapping-config')
        ).getAllByRole('combobox');

        await expect(renderedOptions.length).toBe(2);
        await expect(decisionDefDropdown.value).toBe('');
        await expect(decisionDefVersionDropdown.value).toBe('');
        await expect(dmnVarsDropdown.value).toBe('');
      });
    });

    await step('Removing input mappings', async () => {
      const button = canvas.getByTitle('Verwijderen');

      await userEvent.click(button);

      const varsDropdowns = within(
        document.querySelector('.logic-dmn__mapping-config')
      ).queryAllByRole('combobox');
      const textInput = within(document.querySelector('.logic-dmn__mapping-config')).queryAllByRole(
        'textbox'
      );

      await expect(varsDropdowns.length).toBe(0);
      await expect(textInput.length).toBe(0);
    });

    window.confirm = originalConfirm;
  },
};

export const withInitialValues = {
  args: {
    initialValues: {
      pluginId: 'camunda7',
      decisionDefinitionId: 'approve-payment',
      decisionDefinitionVersion: '1',
      inputMapping: [
        {formVariable: 'name', dmnVariable: 'camundaVar'},
        {formVariable: 'surname', dmnVariable: 'port'},
      ],
      outputMapping: [{formVariable: 'canApply', dmnVariable: 'reason'}],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const pluginDropdown = canvas.getByLabelText('Plugin');

    await expect(pluginDropdown.value).toBe('camunda7');

    const decisionDefDropdown = canvas.getByLabelText('Beslisdefinitie-ID');

    await waitFor(async () => {
      await expect(decisionDefDropdown.value).toBe('approve-payment');
    });

    const decisionDefVersionDropdown = canvas.getByLabelText('Beslisdefinitieversie');

    await waitFor(async () => {
      await expect(decisionDefVersionDropdown.value).toBe('1');
    });

    const varsDropdowns = within(document.querySelector('.logic-dmn__mapping-config')).getAllByRole(
      'combobox'
    );

    // Form vars
    await expect(varsDropdowns[0].value).toBe('name');
    await expect(varsDropdowns[2].value).toBe('surname');
    await expect(varsDropdowns[4].value).toBe('canApply');

    // DMN vars
    await expect(varsDropdowns[1].value).toBe('camundaVar');
    await expect(varsDropdowns[3].value).toBe('port');
    await expect(varsDropdowns[5].value).toBe('reason');
  },
};

export const InvalidEmptyFields = {
  args: {
    initialValues: {
      pluginId: '',
      decisionDefinitionId: '',
      decisionDefinitionVersion: '',
      inputMapping: [],
      outputMapping: [],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const saveButton = within(document.querySelector('.submit-row')).getByRole('button');

    await waitFor(async () => {
      // userEvent.click not working in Firefox here :( https://github.com/testing-library/user-event/issues/1149
      fireEvent.click(saveButton);

      const errorMessages = canvas.getAllByRole('listitem');

      await expect(errorMessages.length).toBe(2);
    });
  },
};

export const OnePluginAvailable = {
  args: {
    availableDMNPlugins: [{id: 'camunda7', label: 'Camunda 7'}],
    initialValues: {
      pluginId: '',
      decisionDefinitionId: '',
      decisionDefinitionVersion: '',
      inputMapping: [],
      outputMapping: [],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const pluginDropdown = canvas.getByLabelText('Plugin');

    await expect(pluginDropdown.value).toBe('camunda7');
  },
};

export const ComplexInputExpressions = {
  args: {
    initialValues: {
      pluginId: 'camunda7',
      decisionDefinitionId: 'withComplexExpressions',
      decisionDefinitionVersion: '1',
      inputMapping: [
        {formVariable: 'postcode', dmnVariable: 'postcode'},
        {formVariable: 'income', dmnVariable: 'a'},
        {formVariable: 'income', dmnVariable: 'b'},
      ],
      outputMapping: [],
    },
  },
};

export const DefinitionChangeResetsMapping = {
  args: {
    initialValues: {
      pluginId: 'camunda7',
      decisionDefinitionId: 'approve-payment',
      decisionDefinitionVersion: '1',
      inputMapping: [
        {formVariable: 'name', dmnVariable: 'camundaVar'},
        {formVariable: 'surname', dmnVariable: 'port'},
      ],
      outputMapping: [{formVariable: 'canApply', dmnVariable: 'reason'}],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    await canvas.findByRole('option', {name: 'Invoice Classification'});

    const formVariableDropdowns = canvas.getAllByRole('combobox', {name: 'Form variable'});
    expect(formVariableDropdowns).toHaveLength(3);

    const definitionDropdown = canvas.getByLabelText('Beslisdefinitie-ID');
    await userEvent.selectOptions(definitionDropdown, 'invoiceClassification');

    expect(canvas.queryAllByRole('combobox', {name: 'Form variable'})).toHaveLength(0);
  },
};

export const VersionChangePartiallyResetsMapping = {
  args: {
    availableDMNPlugins: [{id: 'camunda7', label: 'Camunda 7'}],
    availableFormVariables: [
      {type: 'textfield', key: 'name', name: 'Name'},
      {type: 'textfield', key: 'surname', name: 'Surname'},
      {type: 'postcode', key: 'postcode', name: 'Postcode'},
    ],
    initialValues: {
      pluginId: 'camunda7',
      decisionDefinitionId: 'decision1',
      decisionDefinitionVersion: '1',
      inputMapping: [
        {formVariable: 'name', dmnVariable: 'firstName'},
        {formVariable: 'surname', dmnVariable: 'surname'},
      ],
      outputMapping: [{formVariable: 'postcode', dmnVariable: 'postcodeOutput'}],
    },
  },
  parameters: {
    msw: {
      handlers: [
        mockDMNDecisionDefinitionsGet({camunda7: [{id: 'decision1', label: 'A decision'}]}),
        mockDMNDecisionDefinitionVersionsGet,
        mockDMNParametersGet({
          decision1: {
            _versions: {
              1: {
                inputs: [
                  {
                    label: 'First name',
                    id: 'Input_1',
                    typeRef: 'string',
                    expression: 'firstName',
                  },
                  {
                    label: 'Surname',
                    id: 'InputClause_1cn8gp3',
                    typeRef: 'string',
                    expression: 'surname',
                  },
                ],
                outputs: [
                  {
                    id: 'Output_1',
                    label: 'Postcode',
                    typeRef: 'string',
                    name: 'postcodeOutput',
                  },
                ],
              },
              2: {
                inputs: [
                  {
                    label: 'Full name',
                    id: 'Input_1',
                    typeRef: 'string',
                    expression: 'name',
                  },
                ],
                outputs: [
                  {
                    id: 'Output_1',
                    label: 'Postcode',
                    typeRef: 'string',
                    name: 'postcodeOutput',
                  },
                ],
              },
            },
          },
        }),
      ],
    },
  },
  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);

    await step('initial state', async () => {
      // wait until options have loaded/rendered
      await canvas.findAllByRole('option', {name: 'Surname'});

      const dmnVarDropdowns = canvas.getAllByRole('combobox', {name: 'DMN variable'});
      expect(dmnVarDropdowns).toHaveLength(3);
      // check their values
      expect(dmnVarDropdowns[0]).toHaveValue('firstName');
      expect(dmnVarDropdowns[1]).toHaveValue('surname');
      expect(dmnVarDropdowns[2]).toHaveValue('postcodeOutput');
    });

    await step('Change definition version', async () => {
      const definitionDropdown = canvas.getByLabelText('Beslisdefinitieversie');
      await userEvent.selectOptions(definitionDropdown, '2');

      // wait until options have loaded/rendered
      await canvas.findAllByRole('option', {name: 'Full name'});

      const dmnVarDropdowns = canvas.getAllByRole('combobox', {name: 'DMN variable'});
      expect(dmnVarDropdowns).toHaveLength(3);
      // check their values
      expect(dmnVarDropdowns[0]).toHaveValue('');
      expect(dmnVarDropdowns[1]).toHaveValue('');
      expect(dmnVarDropdowns[2]).toHaveValue('postcodeOutput');
    });

    await step('Submit form', async () => {
      await userEvent.click(canvas.getByRole('button', {name: 'Save'}));

      expect(args.onSave).toHaveBeenCalledWith({
        pluginId: 'camunda7',
        decisionDefinitionId: 'decision1',
        decisionDefinitionVersion: '2',
        inputMapping: [
          {dmnVariable: '', formVariable: 'name'},
          {dmnVariable: '', formVariable: 'surname'},
        ],
        outputMapping: [{dmnVariable: 'postcodeOutput', formVariable: 'postcode'}],
      });
    });
  },
};

export const WarningForEmptyFormVar = {
  args: {
    initialValues: {
      pluginId: 'camunda7',
      decisionDefinitionId: 'approve-payment',
      decisionDefinitionVersion: '1',
      inputMapping: [{formVariable: '', dmnVariable: 'camundaVar'}],
      outputMapping: [{formVariable: '', dmnVariable: 'reason'}],
    },
  },
};
