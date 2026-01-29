import {expect, fireEvent, fn, userEvent, waitFor, within} from 'storybook/test';

import {
  mockDMNDecisionDefinitionVersionsGet,
  mockDMNDecisionDefinitionsGet,
  mockDMNParametersGet,
} from 'components/admin/form_design/mocks';
import {FormDecorator} from 'components/admin/form_design/story-decorators';
import {serializeValue} from 'components/admin/forms/VariableMapping';
import {getReactSelectContainer, rsSelect} from 'utils/storybookTestHelpers';

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
    onSave: fn(),
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
  play: async ({canvasElement, step, args}) => {
    const canvas = within(canvasElement);

    const pluginDropdown = canvas.getByLabelText('Plugin');
    const decisionDefDropdown = canvas.getByLabelText('Beslisdefinitie-ID');
    const decisionDefVersionDropdown = canvas.getByLabelText('Beslisdefinitieversie');

    await step('Selecting plugin, decision definition and version.', async () => {
      await userEvent.selectOptions(pluginDropdown, 'Camunda 7');

      expect(pluginDropdown).toHaveValue('camunda7');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefDropdown).getAllByRole('option');

        expect(renderedOptions.length).toBe(4);
      });

      await userEvent.selectOptions(decisionDefDropdown, 'Approve payment');

      expect(decisionDefDropdown).toHaveValue('approve-payment');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefVersionDropdown).getAllByRole('option');

        expect(renderedOptions.length).toBe(3);
      });

      await userEvent.selectOptions(decisionDefVersionDropdown, 'v2 (version tag: n/a)');

      expect(decisionDefVersionDropdown).toHaveValue('2');
    });

    await step('Adding input mappings', async () => {
      const buttons = canvas.getAllByRole('button');

      await userEvent.click(buttons[0]);

      const dropdowns = within(document.querySelector('.logic-dmn__mapping-config')).getAllByRole(
        'combobox'
      );
      expect(dropdowns.length).toBe(2);

      const [formVarsDropdowns, dmnVarsDropdown] = dropdowns;

      await rsSelect(formVarsDropdowns, 'Name');
      // this is super flaky for some reason on both Chromium and Firefox :/
      await waitFor(async () => {
        await userEvent.selectOptions(dmnVarsDropdown, 'Camunda variable');
        expect(dmnVarsDropdown).toHaveValue(serializeValue('camundaVar'));
      });

      await userEvent.click(canvas.getByRole('button', {name: 'Save'}));
      expect(args.onSave).toHaveBeenCalledWith({
        pluginId: 'camunda7',
        decisionDefinitionId: 'approve-payment',
        decisionDefinitionVersion: '2',
        inputMapping: [{formVariable: 'name', dmnVariable: 'camundaVar'}],
        outputMapping: [],
      });
    });

    await step('Changing plugin clears decision definition, version and DMN vars', async () => {
      await userEvent.selectOptions(pluginDropdown, 'Some other engine');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefDropdown).getAllByRole('option');
        const [, dmnVarsDropdown] = within(
          document.querySelector('.logic-dmn__mapping-config')
        ).getAllByRole('combobox');

        expect(renderedOptions.length).toBe(2);
        expect(decisionDefDropdown).toHaveValue('');
        expect(decisionDefVersionDropdown).toHaveValue('');
        expect(dmnVarsDropdown).toHaveValue('');
      });
    });

    await step('Removing input mappings', async () => {
      const button = canvas.getByTitle('Verwijderen');

      await userEvent.click(button);
      // Close the confirmation modal
      await userEvent.click(
        within(await canvas.findByRole('dialog')).getByRole('button', {
          name: 'Accepteren',
        })
      );

      const varsDropdowns = within(
        document.querySelector('.logic-dmn__mapping-config')
      ).queryAllByRole('combobox');
      const textInput = within(document.querySelector('.logic-dmn__mapping-config')).queryAllByRole(
        'textbox'
      );

      expect(varsDropdowns.length).toBe(0);
      expect(textInput.length).toBe(0);
    });
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
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    await step('Selected plugin', async () => {
      const pluginDropdown = canvas.getByLabelText('Plugin');
      const option = await within(pluginDropdown).findByRole('option', {name: 'Camunda 7'});
      expect(option.selected).toBe(true);
    });

    await step('Decision definition', async () => {
      const decisionDefDropdown = canvas.getByLabelText('Beslisdefinitie-ID');
      const option = await within(decisionDefDropdown).findByRole('option', {
        name: 'Approve payment',
      });
      expect(option.selected).toBe(true);
    });

    await step('Decision definition versions', async () => {
      const decisionDefVersionDropdown = canvas.getByLabelText('Beslisdefinitieversie');
      const option = await within(decisionDefVersionDropdown).findByRole('option', {
        name: 'v1 (version tag: n/a)',
      });
      expect(option.selected).toBe(true);
    });

    await step('Form variable dropdown values', async () => {
      const formVariableDropdowns = await canvas.findAllByLabelText('Formuliervariabele');

      await waitFor(async () => {
        expect(
          await within(getReactSelectContainer(formVariableDropdowns[0])).findByText('Name')
        ).toBeVisible();
        expect(
          await within(getReactSelectContainer(formVariableDropdowns[1])).findByText('Surname')
        ).toBeVisible();
        expect(
          await within(getReactSelectContainer(formVariableDropdowns[2])).findByText('Can apply?')
        ).toBeVisible();
      });
    });

    await step('DMN variable dropdown values', async () => {
      const dmnVariableDropdowns = await canvas.findAllByLabelText('DMN-variabele');

      await waitFor(async () => {
        expect(dmnVariableDropdowns[0]).toHaveValue(serializeValue('camundaVar'));
        expect(dmnVariableDropdowns[1]).toHaveValue(serializeValue('port'));
        expect(dmnVariableDropdowns[2]).toHaveValue(serializeValue('reason'));
      });
    });
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

      expect(errorMessages.length).toBe(2);
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

    expect(pluginDropdown).toHaveValue('camunda7');
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

    const formVariableDropdowns = canvas.getAllByRole('combobox', {name: 'Formuliervariabele'});
    expect(formVariableDropdowns).toHaveLength(3);

    const definitionDropdown = canvas.getByLabelText('Beslisdefinitie-ID');
    await userEvent.selectOptions(definitionDropdown, 'invoiceClassification');

    expect(canvas.queryAllByRole('combobox', {name: 'Formuliervariabele'})).toHaveLength(0);
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

      const dmnVarDropdowns = canvas.getAllByRole('combobox', {name: 'DMN-variabele'});
      expect(dmnVarDropdowns).toHaveLength(3);
      // check their values
      expect(dmnVarDropdowns[0]).toHaveValue(serializeValue('firstName'));
      expect(dmnVarDropdowns[1]).toHaveValue(serializeValue('surname'));
      expect(dmnVarDropdowns[2]).toHaveValue(serializeValue('postcodeOutput'));
    });

    await step('Change definition version', async () => {
      const definitionDropdown = canvas.getByLabelText('Beslisdefinitieversie');
      await userEvent.selectOptions(definitionDropdown, '2');

      // wait until options have loaded/rendered
      await canvas.findAllByRole('option', {name: 'Full name'});

      const dmnVarDropdowns = canvas.getAllByRole('combobox', {name: 'DMN-variabele'});
      expect(dmnVarDropdowns).toHaveLength(3);
      // check their values
      expect(dmnVarDropdowns[0]).toHaveValue('');
      expect(dmnVarDropdowns[1]).toHaveValue('');
      expect(dmnVarDropdowns[2]).toHaveValue(serializeValue('postcodeOutput'));
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
