import {useArgs} from '@storybook/preview-api';

import {FormDecorator} from 'components/admin/form_design/story-decorators';

import VariableSelection from './VariableSelection';

const render = ({name, includeStaticVariables, filter}) => {
  const [{value}, updateArgs] = useArgs();
  return (
    <VariableSelection
      name={name}
      value={value}
      includeStaticVariables={includeStaticVariables}
      onChange={event => updateArgs({value: event.target.value})}
      filter={filter}
    />
  );
};

export default {
  title: 'Form design/VariableSelection',
  component: VariableSelection,
  decorators: [FormDecorator],
  render,

  args: {
    name: 'variableSelection',
    value: 'key2',
    includeStaticVariables: true,
    filter: () => true,

    availableFormSteps: [
      {
        configuration: {
          display: 'form',
        },

        formDefinition: 'foo',
        slug: '',
        url: '',
        _generatedId: '',
        isNew: true,
        validationErrors: [],
      },
    ],

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
    availableFormSteps: {
      table: {
        disable: true,
      },
    },

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

export const Default = {};
