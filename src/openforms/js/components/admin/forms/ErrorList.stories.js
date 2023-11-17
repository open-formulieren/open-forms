import ErrorList from './ErrorList';

export default {
  title: 'Admin/Django/ErrorList',
  component: ErrorList,

  args: {
    classNamePrefix: '',
    classNameModifier: '',
    children: ['Error #1', 'Error #2'],
  },
};

export const ListOfErrorStrings = {
  name: 'List of error strings',

  args: {
    children: ['Error #1', 'Error #2'],
  },
};

export const NoErrors = {
  name: 'No errors',

  args: {
    children: [],
  },
};

export const SingleError = {
  name: 'Single error',

  args: {
    children: 'single error',
  },
};
