import {Radio} from './Inputs';
import RadioList from './RadioList';

export default {
  title: 'Admin/Django/RadioList',
  component: RadioList,
};

export const Default = {
  name: 'Default',

  args: {
    children: [<Radio name="foo" label="foo" />, <Radio name="bar" label="bar" />],
  },
};
