import {AdminChangeFormDecorator} from 'components/admin/form_design/story-decorators';

import Field from './Field';
import FormRow from './FormRow';
import {TextInput} from './Inputs';

export default {
  title: 'Admin/Django/FormRow',
  component: FormRow,
  decorators: [AdminChangeFormDecorator],
  parameters: {
    adminChangeForm: {
      wrapFieldset: true,
    },
  },
};

export const SingleField = {
  render: () => (
    <FormRow fields={['field1']}>
      <Field errors={['Foo']} name="field1" label="Input field" helpText="Lorem ipsum">
        <TextInput />
      </Field>
    </FormRow>
  ),

  name: 'Single field',
};

export const MultipleFields = {
  render: () => (
    <FormRow fields={['field1', 'field2']}>
      <Field
        fieldBox
        errors={['some error']}
        name="field1"
        label="Input field 1"
        helpText="Lorem ipsum"
      >
        <TextInput />
      </Field>
      <Field fieldBox name="field2" label="Input field 2" helpText="Lorem ipsum">
        <TextInput />
      </Field>
    </FormRow>
  ),

  name: 'Multiple fields',
};
