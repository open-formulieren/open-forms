import {fn} from 'storybook/test';

import JsonWidget from './JsonWidget';

export default {
  title: 'Admin/Custom/JsonWidget',
  component: JsonWidget,
  args: {
    name: 'some-json',
    logic: {
      '==': [1, 1],
    },
    onChange: fn(),
    cols: 40,
    isExpanded: true,
  },
};

export const Default = {};
