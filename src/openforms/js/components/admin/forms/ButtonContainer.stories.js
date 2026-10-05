import {fn} from 'storybook/test';

import ButtonContainer from './ButtonContainer';

export default {
  title: 'Admin/Custom/ButtonContainer',
  component: ButtonContainer,
  args: {
    children: 'Add',
    onClick: fn(),
  },
};

export const Default = {};
