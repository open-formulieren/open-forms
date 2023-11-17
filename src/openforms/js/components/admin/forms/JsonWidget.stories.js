import JsonWidget from './JsonWidget';

export default {
  title: 'Admin/Custom/JsonWidget',
  component: JsonWidget,
};

export const Default = {
  name: 'Default',

  args: {
    name: 'JsonWidget',

    logic: {
      '==': [1, 1],
    },

    onChange: (...args) => {
      null;
    },

    cols: 40,
    isExpanded: true,
  },
};
