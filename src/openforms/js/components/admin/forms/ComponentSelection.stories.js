import {FormDecorator} from 'components/admin/form_design/story-decorators';

import ComponentSelection from './ComponentSelection';

export default {
  title: 'Form design/ComponentSelection',
  component: ComponentSelection,
  decorators: [FormDecorator],
  args: {
    name: 'componentSelect',
    value: 'foo',
    // decorator args
    availableComponents: {
      foo: {
        label: 'Foo',
      },
      bar: {
        label: 'Bar',
      },
    },
  },
};

export const Default = {};
