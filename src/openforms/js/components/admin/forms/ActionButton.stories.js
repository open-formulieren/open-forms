import {ActionButton, AddAnotherAction, ContinueEditingAction, SubmitAction} from './ActionButton';

export default {
  title: 'Admin/Django/ActionButton',
  component: ActionButton,
};

export const ActionButtonDefault = {
  name: 'ActionButton default',
  component: ActionButton,

  args: {
    name: '',
    text: 'Save',
  },
};

export const SubmitActionStory = {
  name: 'SubmitAction',
  component: SubmitAction,
};

export const AddAnotherActionStory = {
  name: 'AddAnotherAction',
  component: AddAnotherAction,
};

export const ContinueEditingActionStory = {
  name: 'ContinueEditingAction',
  component: ContinueEditingAction,
};
