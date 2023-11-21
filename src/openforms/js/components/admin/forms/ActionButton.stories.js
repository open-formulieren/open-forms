import {ActionButton, AddAnotherAction, ContinueEditingAction, SubmitAction} from './ActionButton';

export default {
  title: 'Admin/Django/ActionButton',
  component: ActionButton,
};

export const ActionButtonDefault = {
  name: 'ActionButton default',

  args: {
    name: '',
    text: 'Save',
  },
};

export const SubmitActionStory = {
  name: 'SubmitAction',
  render: () => <SubmitAction />,
};

export const AddAnotherActionStory = {
  name: 'AddAnotherAction',
  render: () => <AddAnotherAction />,
};

export const ContinueEditingActionStory = {
  name: 'ContinueEditingAction',
  render: () => <ContinueEditingAction />,
};
