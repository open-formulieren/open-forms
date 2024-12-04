import {FormikDecorator} from 'components/admin/form_design/story-decorators';

import TargetPathSelect from './TargetPathSelect';

export default {
  title: 'Form design / TargetPathSelect',
  component: TargetPathSelect,
  decorators: [FormikDecorator],
  args: {
    name: 'someTarget',
    isLoading: false,
    targetPaths: [
      {
        targetPath: ['root', 'child'],
        isRequired: false,
      },
      {
        targetPath: ['root', 'other child'],
        isRequired: true,
      },
    ],
    isDisabled: false,
  },
  parameters: {
    formik: {
      initialValues: {
        someTarget: null,
      },
    },
  },
};

export const Default = {};

export const ValueSelected = {
  parameters: {
    formik: {
      initialValues: {
        someTarget: ['root', 'other child'],
      },
    },
  },
};
