import Select from './Select';

export default {
  title: 'Admin/Django/Select',
  component: Select,
  args: {
    name: 'select',
    choices: [
      ['foo', 'Foo'],
      ['bar', 'Bar'],
    ],
    allowBlank: false,
    translateChoices: false,
  },
};

export const Default = {};
