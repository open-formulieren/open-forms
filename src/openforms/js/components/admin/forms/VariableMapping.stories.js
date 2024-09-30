import {expect, fn, within} from '@storybook/test';
import {Formik} from 'formik';

import {FormDecorator} from 'components/admin/form_design/story-decorators';

import VariableMapping from './VariableMapping';

const render = ({name, includeStaticVariables, alreadyMapped}) => {
  return (
    <Formik
      initialValues={{mapping: [{variableName: 'foo', prefillAttribute: 'bar'}]}}
      onSubmit={fn()}
    >
      <VariableMapping
        loading={false}
        mappingName="mapping"
        targets={[
          [['nested', 'property'], 'Nested > property'],
          [['otherProperty'], 'Other property'],
        ]}
        targetsFieldName="targets"
        targetsColumnLabel="Prefill property"
        selectAriaLabel="Prefill property"
        includeStaticVariables={includeStaticVariables}
        alreadyMapped={alreadyMapped}
      />
    </Formik>
  );
};

export default {
  title: 'Form design/VariableMapping',
  component: VariableMapping,
  decorators: [FormDecorator],
  render,

  args: {
    name: 'VariableMapping',
    value: 'key2',
    includeStaticVariables: false,
    filter: () => true,

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

    const formVariableDropdown = canvas.getByLabelText('Formuliervariabele');
    const variableOptions = within(formVariableDropdown).getAllByRole('option');

    await expect(variableOptions).toHaveLength(2);
    await expect(variableOptions[1]).toHaveValue('key2');

    const targetDropdown = canvas.getByLabelText('Prefill property');
    const targetOptions = within(targetDropdown).getAllByRole('option');

    await expect(targetOptions).toHaveLength(3);
    await expect(targetOptions[1]).toHaveValue('nested,property');
    await expect(targetOptions[2]).toHaveValue('otherProperty');
  },
};

export const WithStaticVariables = {
  args: {
    includeStaticVariables: true,
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const formVariableDropdown = canvas.getByLabelText('Formuliervariabele');
    const variableOptions = within(formVariableDropdown).getAllByRole('option');

    await expect(variableOptions).toHaveLength(3);
    await expect(variableOptions[1]).toHaveValue('key1');
    await expect(variableOptions[2]).toHaveValue('key2');

    const targetDropdown = canvas.getByLabelText('Prefill property');
    const targetOptions = within(targetDropdown).getAllByRole('option');

    await expect(targetOptions).toHaveLength(3);
    await expect(targetOptions[1]).toHaveValue('nested,property');
    await expect(targetOptions[2]).toHaveValue('otherProperty');
  },
};

export const WithAlreadyMappedTargets = {
  args: {
    alreadyMapped: [['otherProperty']],
  },
  play: async ({canvasElement}) => {
    const canvas = within(canvasElement);

    const formVariableDropdown = canvas.getByLabelText('Formuliervariabele');
    const variableOptions = within(formVariableDropdown).getAllByRole('option');

    await expect(variableOptions).toHaveLength(2);
    await expect(variableOptions[1]).toHaveValue('key2');

    const targetDropdown = canvas.getByLabelText('Prefill property');
    const targetOptions = within(targetDropdown).getAllByRole('option');

    await expect(targetOptions).toHaveLength(2);
    await expect(targetOptions[1]).toHaveValue('nested,property');
  },
};
