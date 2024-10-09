import {expect, fn, userEvent, within} from '@storybook/test';
import selectEvent from 'react-select-event';

import {FormDecorator, FormikDecorator} from 'components/admin/form_design/story-decorators';
import {getReactSelectOptions} from 'utils/storybookTestHelpers';

import VariableMapping, {serializeValue} from './VariableMapping';

export default {
  title: 'Form design/VariableMapping',
  component: VariableMapping,
  decorators: [FormikDecorator, FormDecorator],

  parameters: {
    formik: {
      initialValues: {
        mapping: [{formVariable: 'key2', property: 'option_2'}],
      },
    },
  },

  args: {
    loading: false,
    name: 'mapping',
    propertyName: 'property',
    propertyChoices: [
      ['option_1', 'Option 1'],
      ['option_2', 'Option 2'],
    ],
    propertyHeading: 'Property',
    propertySelectLabel: 'Pick a property',
    includeStaticVariables: false,

    availableStaticVariables: [
      {
        form: 'foo',
        formDefinition: 'foo',
        name: 'name1',
        key: 'key1',
      },
    ],

    availableFormVariables: [
      {
        form: 'bar',
        formDefinition: 'bar',
        name: 'name2',
        key: 'key2',
      },
    ],
  },
  argTypes: {
    availableStaticVariables: {
      table: {
        disable: true,
      },
    },
    availableFormVariables: {
      table: {
        disable: true,
      },
    },
  },
};

export const Default = {
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);
    const form = canvas.getByTestId('story-form');
    expect(form).toHaveFormValues({
      'mapping.0.formVariable': 'key2',
      'mapping.0.property': serializeValue('option_2'),
    });
  },
};

export const NonStringValues = {
  render: args => (
    <>
      <VariableMapping {...args} />
      <button type="submit">Submit</button>
    </>
  ),

  args: {
    propertyChoices: [
      [['nested', 'property'], 'Nested > property'],
      [['otherProperty'], 'Other property'],
    ],
  },

  parameters: {
    formik: {
      initialValues: {
        mapping: [{formVariable: 'key2', property: ['nested', 'property']}],
      },
      onSubmit: fn(),
    },
  },

  play: async ({canvasElement, parameters}) => {
    const canvas = within(canvasElement);
    const form = canvas.getByTestId('story-form');
    expect(form).toHaveFormValues({
      'mapping.0.formVariable': 'key2',
      'mapping.0.property': serializeValue(['nested', 'property']),
    });

    await userEvent.click(canvas.getByRole('button', {name: 'Submit'}));
    const mockSubmit = parameters.formik.onSubmit;
    expect(mockSubmit).toHaveBeenCalledOnce();
    const values = mockSubmit.mock.lastCall[0];
    expect(values).toEqual({
      mapping: [
        {
          formVariable: 'key2',
          property: ['nested', 'property'],
        },
      ],
    });
  },
};

export const SelectOptions = {
  render: args => (
    <>
      <VariableMapping {...args} includeStaticVariables />
      <button type="submit">Submit</button>
    </>
  ),

  parameters: {
    formik: {
      onSubmit: fn(),
    },
  },

  play: async ({canvasElement, parameters, step}) => {
    const canvas = within(canvasElement);

    await step('Check rendered values', async () => {
      const formVariableDropdown = canvas.getByLabelText('Formuliervariabele');
      await selectEvent.openMenu(formVariableDropdown);
      const variableOptions = getReactSelectOptions(formVariableDropdown);

      await expect(variableOptions).toHaveLength(2);
      await expect(variableOptions[1]).toHaveTextContent('(key2)');

      const propertyDropdown = canvas.getByLabelText('Pick a property');
      const propertyOptions = within(propertyDropdown).getAllByRole('option');

      await expect(propertyOptions).toHaveLength(3);
      await expect(propertyOptions[1]).toHaveValue(serializeValue('option_1'));
      await expect(propertyOptions[2]).toHaveValue(serializeValue('option_2'));
    });

    await step('Select different option and submit', async () => {
      const propertyDropdown = canvas.getByLabelText('Pick a property');
      await userEvent.selectOptions(propertyDropdown, 'Option 1');
      await userEvent.click(canvas.getByRole('button', {name: 'Submit'}));
      const mockSubmit = parameters.formik.onSubmit;
      expect(mockSubmit).toHaveBeenCalledOnce();
      const values = mockSubmit.mock.lastCall[0];
      expect(values).toEqual({
        mapping: [
          {
            formVariable: 'key2',
            property: 'option_1',
          },
        ],
      });
    });
  },
};

export const WithStaticVariables = {
  args: {
    includeStaticVariables: true,
  },
};

export const OmitAlreadyMappedValues = {
  parameters: {
    formik: {
      initialValues: {
        mapping: [
          {formVariable: 'key2', property: 'option_2'},
          {formVariable: '', property: ''},
        ],
      },
    },
  },
  play: async ({canvasElement, step}) => {
    const canvas = within(canvasElement);

    const formVariableDropdowns = canvas.getAllByLabelText('Pick a property');

    await step('first row', async () => {
      const firstDropdown = formVariableDropdowns[0];
      const option1 = within(firstDropdown).getByRole('option', {name: 'Option 1'});
      expect(option1).toBeVisible();
      const option2 = within(firstDropdown).getByRole('option', {name: 'Option 2'});
      expect(option2).toBeVisible();
    });

    await step('second row', async () => {
      const secondDropdown = formVariableDropdowns[1];
      const option1 = within(secondDropdown).getByRole('option', {name: 'Option 1'});
      expect(option1).toBeVisible();
      const option2 = within(secondDropdown).queryByRole('option', {name: 'Option 2'});
      expect(option2).toBeNull();
    });
  },
};
