import {fn} from 'storybook/test';

import DeleteIcon from './DeleteIcon';

export default {
  title: 'Admin / Custom / Icons / Delete',
  component: DeleteIcon,
  args: {
    onConfirm: fn(),
  },
};

export const Delete = {};
