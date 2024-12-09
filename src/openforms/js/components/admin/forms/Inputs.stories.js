import flatpickr from 'flatpickr';

import {AdminChangeFormDecorator} from 'components/admin/form_design/story-decorators';

import {
  Checkbox,
  DateInput,
  DateTimeInput,
  Input,
  NumberInput,
  Radio,
  TextArea,
  TextInput,
} from './Inputs';

export default {
  title: 'Admin/Django/Inputs',
  component: Input,
};

export const CheckboxStory = {
  name: 'Checkbox',
  render: args => <Checkbox {...args} />,

  decorators: [AdminChangeFormDecorator],
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
  },

  args: {
    name: 'Checkbox',
    label: 'Checkbox',
    helpText: 'Foo bar baz',
    disabled: false,
  },
};

export const DateInputStory = {
  name: 'DateInput',
  render: args => <DateInput {...args} />,

  args: {
    name: 'DateInput',
  },
};

export const DateTimeInputStory = {
  name: 'DateTimeInput',
  render: args => <DateTimeInput {...args} />,

  args: {
    name: 'DateTimeInput',
    value: '2022-01-01T12:00:00',
  },
};

export const InputStory = {
  name: 'Input',
  render: args => <Input {...args} />,

  args: {
    name: 'Input',
    type: 'text',
  },
};

export const NumberInputStory = {
  name: 'NumberInput',
  render: args => <NumberInput {...args} />,

  args: {
    name: 'NumberInput',
  },
};

export const RadioStory = {
  name: 'Radio',
  render: args => <Radio {...args} />,

  args: {
    name: 'Radio',
    idFor: 'foo',
    label: 'Radio',
    helpText: 'Foo bar baz',
  },
};

export const TextAreaStory = {
  name: 'TextArea',
  render: args => <TextArea {...args} />,

  args: {
    name: 'TextArea',
    rows: 5,
    cols: 20,
  },
};

export const TextInputStory = {
  name: 'TextInput',
  render: args => <TextInput {...args} />,

  args: {
    name: 'TextInput',
    noVTextField: true,
  },
};
