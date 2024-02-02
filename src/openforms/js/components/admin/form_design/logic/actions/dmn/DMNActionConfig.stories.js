import {expect} from '@storybook/jest';
import {fireEvent, userEvent, waitFor, within} from '@storybook/testing-library';

import {
  mockDMNDecisionDefinitionVersionsGet,
  mockDMNDecisionDefinitionsGet,
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
          ],
          'some-other-engine': [{id: 'some-definition-id', label: 'Some definition id'}],
        }),
        mockDMNDecisionDefinitionVersionsGet,
      ],
    },
  },
};

export const DefaultEmpty = {
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

    const pluginDropdown = canvas.getByLabelText('Plugin ID');
    const decisionDefDropdown = canvas.getByLabelText('Decision definition ID');
    const decisionDefVersionDropdown = canvas.getByLabelText('Decision definition version');

    await step('Selecting plugin, decision definition and version.', async () => {
      await userEvent.selectOptions(pluginDropdown, 'Camunda 7');

      await expect(pluginDropdown.value).toBe('camunda7');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefDropdown).getAllByRole('option');

        await expect(renderedOptions.length).toBe(3);
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

    await step('Changing plugin clears decision definition and version.', async () => {
      await userEvent.selectOptions(pluginDropdown, 'Some other engine');

      await waitFor(async () => {
        const renderedOptions = within(decisionDefDropdown).getAllByRole('option');

        await expect(renderedOptions.length).toBe(2);
        await expect(decisionDefDropdown.value).toBe('');
        await expect(decisionDefVersionDropdown.value).toBe('');
      });
    });

    await step('Adding input mappings', async () => {
      const buttons = canvas.getAllByRole('button');

      await userEvent.click(buttons[0]);

      const varsDropdowns = within(document.querySelector('.mappings')).getAllByRole('combobox');
      const textInput = within(document.querySelector('.mappings')).getAllByRole('textbox');

      await expect(varsDropdowns.length).toBe(1);
      await expect(textInput.length).toBe(1);

      await userEvent.selectOptions(varsDropdowns[0], 'Name');
      await userEvent.type(textInput[0], 'NameDMN');

      await expect(varsDropdowns[0].value).toBe('name');
      await expect(textInput[0].value).toBe('NameDMN');
    });

    await step('Removing input mappings', async () => {
      const button = canvas.getByTitle('Verwijderen');

      await userEvent.click(button);

      const varsDropdowns = within(document.querySelector('.mappings')).queryAllByRole('combobox');
      const textInput = within(document.querySelector('.mappings')).queryAllByRole('textbox');

      await expect(varsDropdowns.length).toBe(0);
      await expect(textInput.length).toBe(0);
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
        {formVar: 'name', dmnVar: 'dmnName'},
        {formVar: 'surname', dmnVar: 'dmnSurname'},
      ],
      outputMapping: [{formVar: 'canApply', dmnVar: 'dmnCanApply'}],
    },
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);
    const originalConfirm = window.confirm;
    window.confirm = () => true;

    const pluginDropdown = canvas.getByLabelText('Plugin ID');

    await expect(pluginDropdown.value).toBe('camunda7');

    const decisionDefDropdown = canvas.getByLabelText('Decision definition ID');

    await waitFor(async () => {
      await expect(decisionDefDropdown.value).toBe('approve-payment');
    });

    const decisionDefVersionDropdown = canvas.getByLabelText('Decision definition version');

    await waitFor(async () => {
      await expect(decisionDefVersionDropdown.value).toBe('1');
    });

    const varsDropdowns = within(document.querySelector('.mappings')).getAllByRole('combobox');

    await expect(varsDropdowns[0].value).toBe('name');
    await expect(varsDropdowns[1].value).toBe('surname');
    await expect(varsDropdowns[2].value).toBe('canApply');

    const textFields = within(document.querySelector('.mappings')).getAllByRole('textbox');

    await expect(textFields[0].value).toBe('dmnName');
    await expect(textFields[1].value).toBe('dmnSurname');
    await expect(textFields[2].value).toBe('dmnCanApply');

    window.confirm = originalConfirm;
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
