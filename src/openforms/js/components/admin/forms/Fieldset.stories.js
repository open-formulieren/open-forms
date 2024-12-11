import {AdminChangeFormDecorator} from 'components/admin/form_design/story-decorators';

import Field from './Field';
import Fieldset from './Fieldset';
import FormRow from './FormRow';
import {TextInput} from './Inputs';

const render = ({title, extraClassName = ''}) => (
  <Fieldset title={title} extraClassName={extraClassName}>
    {/* typical example of nested content */}
    <FormRow>
      <Field name="Field" label="Input field" helpText="Lorem ipsum">
        <TextInput />
      </Field>
    </FormRow>
    <FormRow>
      <Field name="Field2" label="Input field2" helpText="Lorem ipsum">
        <TextInput />
      </Field>
    </FormRow>
  </Fieldset>
);

export default {
  title: 'Admin/Django/Fieldset',
  component: Fieldset,
  render,
  decorators: [AdminChangeFormDecorator],

  argTypes: {
    children: {
      table: {
        disable: true,
      },
    },
  },
};

export const Default = {
  name: 'Default',

  args: {
    title: 'The fieldset title',
    extraClassName: '',
  },
};

export const WithoutTitle = {
  name: 'Without title',

  args: {
    title: '',
    extraClassName: '',
  },
};
