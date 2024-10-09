import {within} from '@storybook/test';

const getReactSelectInput = SelectElement => {
  return SelectElement.closest('.admin-react-select').querySelector('input[type="hidden"]');
};

const getReactSelectOptions = SelectElement => {
  return within(SelectElement.closest('.admin-react-select')).getAllByRole('option');
};

export {getReactSelectInput, getReactSelectOptions};
