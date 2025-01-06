import BooleanIcon, {IconNo, IconUnknown, IconYes} from './BooleanIcons';

export default {
  title: 'Admin / Django / BooleanIcons',
  component: BooleanIcon,
};

export const Yes = {
  render: () => <IconYes />,
};

export const No = {
  render: () => <IconNo />,
};

export const Unknown = {
  render: () => <IconUnknown />,
};
