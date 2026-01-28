import {useArgs} from 'storybook/preview-api';

import {FormDecorator} from 'components/admin/form_design/story-decorators';

import {VARIABLE_SOURCES} from '../form_design/variables/constants';
import {ReactSelectContext} from './ReactSelect';
import VariableSelection from './VariableSelection';

// workaround for https://github.com/JedWatson/react-select/issues/3708
const resetParentSelector = Story => (
  <ReactSelectContext.Provider value={{parentSelector: () => undefined}}>
    <Story />
  </ReactSelectContext.Provider>
);

const render = ({
  name,
  includeStaticVariables,
  filter,
  menuIsOpen = false,
  isMulti = false,
  isClearable = false,
}) => {
  const [{value}, updateArgs] = useArgs();
  return (
    <VariableSelection
      name={name}
      value={value}
      includeStaticVariables={includeStaticVariables}
      onChange={event => updateArgs({value: event.target.value})}
      filter={filter}
      menuIsOpen={menuIsOpen}
      isMulti={isMulti}
      isClearable={isClearable}
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
        formDefinition: 'foo',
        name: 'Form step foo',
        slug: '',
        url: '',
        _generatedId: '',
        isNew: true,
        validationErrors: [],
      },
      {
        formDefinition: 'bar',
        name: 'bar',
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
        formDefinition: '',
        name: 'Name 1',
        key: 'key1',
        source: VARIABLE_SOURCES.static,
      },
    ],

    availableFormVariables: [
      {
        form: 'bar',
        formDefinition: 'foo',
        name: 'Name 2',
        key: 'key2',
        source: VARIABLE_SOURCES.component,
      },
      {
        form: 'bar',
        formDefinition: 'foo',
        name: 'Name 5, which is rather long compared to the other names, and wraps',
        key: 'key5',
        source: VARIABLE_SOURCES.component,
      },
      {
        form: 'bar',
        formDefinition: '',
        name: 'Name 3',
        key: 'key3',
        source: VARIABLE_SOURCES.userDefined,
      },
      {
        form: 'bar',
        formDefinition: '',
        name: 'Name 4, which is rather long compared to the other names, and wraps',
        key: 'key4',
        source: VARIABLE_SOURCES.userDefined,
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

export const menuOpen = {
  decorators: [resetParentSelector],
  args: {
    menuIsOpen: true,
  },
};

export const multiSelection = {
  decorators: [resetParentSelector],
  args: {
    value: ['key2', 'key5'],
    menuIsOpen: true,
    isMulti: true,
  },
};

export const Clearable = {
  args: {
    isClearable: true,
  },
};
