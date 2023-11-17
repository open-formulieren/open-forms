import flatpickr from 'flatpickr';

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
  component: Checkbox,

  args: {
    name: 'Checkbox',
    label: 'Checkbox',
    helpText: 'Foo bar baz',
    disabled: false,
  },
};

export const DateInputStory = {
  name: 'DateInput',
  component: DateInput,

  args: {
    name: 'DateInput',
  },
};

export const DateTimeInputStory = {
  name: 'DateTimeInput',
  component: DateTimeInput,

  args: {
    name: 'DateTimeInput',
    value: '2022-01-01T12:00:00',
  },
};

export const InputStory = {
  name: 'Input',
  component: Input,

  args: {
    name: 'Input',
    type: 'text',
  },
};

export const NumberInputStory = {
  name: 'NumberInput',
  component: NumberInput,

  args: {
    name: 'NumberInput',
  },
};

export const RadioStory = {
  name: 'Radio',
  component: Radio,

  args: {
    name: 'Radio',
    idFor: 'foo',
    label: 'Radio',
    helpText: 'Foo bar baz',
  },
};

export const TextAreaStory = {
  name: 'TextArea',
  component: TextArea,

  args: {
    name: 'TextArea',
    rows: 5,
    cols: 20,
  },
};

export const TextInputStory = {
  name: 'TextInput',
  component: TextInput,

  args: {
    name: 'TextInput',
    noVTextField: true,
  },
};
