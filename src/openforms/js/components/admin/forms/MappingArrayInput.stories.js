import {useArgs} from 'storybook/preview-api';

import MappingArrayInput from './MappingArrayInput';

const render = ({
  name,
  inputType,
  deleteConfirmationMessage,
  addButtonMessage,
  valueArrayInput,
}) => {
  const [{currentValue}, updateArgs] = useArgs();
  return (
    <MappingArrayInput
      name={name}
      inputType={inputType}
      mapping={currentValue}
      onChange={event => updateArgs({currentValue: event.target.value})}
      deleteConfirmationMessage={deleteConfirmationMessage}
      addButtonMessage={addButtonMessage}
      valueArrayInput={valueArrayInput}
    />
  );
};

export default {
  title: 'Admin/Custom/MappingArrayInput',
  component: MappingArrayInput,
  render,

  argTypes: {
    mapping: {
      table: {
        disable: true,
      },
    },

    onChange: {
      table: {
        disable: true,
      },
    },
  },
};

export const FlatMapping = {
  name: 'Flat mapping',

  args: {
    name: 'field',
    inputType: 'text',
    currentValue: [
      ['Header1', 'value1'],
      ['Header2', 'value2'],
    ],
    deleteConfirmationMessage: 'Are you sure you want to delete this?',
    addButtonMessage: 'Add more',
    valueArrayInput: false,
  },
};

export const NestedListsMapping = {
  name: 'Nested lists mapping',

  args: {
    name: 'field',
    currentValue: [
      ['Header1', ['value1', 'value2']],
      ['Header2', ['value3']],
    ],
    deleteConfirmationMessage: 'Are you sure you want to delete this?',
    addButtonMessage: 'Add more',
    valueArrayInput: true,
    inputType: 'text',
  },
};
