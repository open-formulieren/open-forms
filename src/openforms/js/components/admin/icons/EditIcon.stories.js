import {fn} from 'storybook/test';

import EditIcon from './EditIcon';

export default {
  title: 'Admin / Custom / Icons / Edit',
  component: EditIcon,
  args: {
    label: 'Edit my thing!',
    onClick: fn(),
  },
};

export const Edit = {};
