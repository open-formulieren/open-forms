import DataPreview from './DataPreview';

export default {
  title: 'Form Design / Components / DSLDataPreview',
  component: DataPreview,
  args: {
    data: {
      type: 'some-type-key',
      foo: ['bar', 42],
    },
    maxRows: 20,
  },
};

export const Default = {};
