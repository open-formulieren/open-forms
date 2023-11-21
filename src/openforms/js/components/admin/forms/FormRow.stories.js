import Field from './Field';
import Fieldset from './Fieldset';
import FormRow from './FormRow';
import {TextInput} from './Inputs';

const FormDecorator = Story => (
  <form>
    <Fieldset>
      <Story />
    </Fieldset>
  </form>
);

export default {
  title: 'Admin/Django/FormRow',
  component: FormRow,
  decorators: [FormDecorator],
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
