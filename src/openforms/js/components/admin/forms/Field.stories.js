import {AdminChangeFormDecorator} from 'components/admin/form_design/story-decorators';

import Field from './Field';
import {TextInput} from './Inputs';

export default {
  title: 'Admin/Django/Field',
  component: Field,

  decorators: [
    Story => (
      <div class="form-row">
        <Story />
      </div>
    ),
    AdminChangeFormDecorator,
    Story => (
      <div class="react-form-create">
        <Story />
      </div>
    ),
  ],
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
  },

  args: {
    children: <TextInput />,
  },

  argTypes: {
    children: {
      control: {
        disable: true,
      },
    },
  },
};

export const Default = {
  args: {
    name: 'Field',
    label: 'Input field',
    helpText: 'Lorem ipsum',
    errorClassPrefix: '',
    errorClassModifier: '',
  },
};

export const HasErrors = {
  name: 'Has errors',

  args: {
    name: 'Field',
    label: 'Field label',
    helpText: 'Lorem ipsum',
    errors: ['Foo is missing'],
  },
};

export const Disabled = {
  args: {
    name: 'Field',
    label: 'Field label',
    helpText: 'Lorem ipsum',
    disabled: true,
  },
};

export const Required = {
  args: {
    name: 'Field',
    label: 'Field label',
    helpText: 'Lorem ipsum',
    required: true,
  },
};
