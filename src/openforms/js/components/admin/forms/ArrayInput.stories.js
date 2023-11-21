import ArrayInput from './ArrayInput';

export default {
  title: 'Admin/Custom/ArrayInput',
  component: ArrayInput,
  args: {
    name: 'field',
    inputType: 'text',
    values: ['foo', 'bar'],
    deleteConfirmationMessage: 'Are you sure you want to delete this?',
    addButtonMessage: 'Add more',
  },
};

export const Default = {};
