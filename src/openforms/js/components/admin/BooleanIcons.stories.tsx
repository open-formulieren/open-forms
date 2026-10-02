import type {Meta, StoryObj} from '@storybook/react-vite';

import BooleanIcon, {IconNo, IconUnknown, IconYes} from './BooleanIcons';

export default {
  title: 'Admin / Django / BooleanIcons',
  component: BooleanIcon,
} satisfies Meta<typeof BooleanIcon>;

export const Yes: StoryObj<typeof IconYes> = {
  render: () => <IconYes />,
};

export const No: StoryObj<typeof IconNo> = {
  render: () => <IconNo />,
};

export const Unknown: StoryObj<typeof IconUnknown> = {
  render: () => <IconUnknown />,
};
