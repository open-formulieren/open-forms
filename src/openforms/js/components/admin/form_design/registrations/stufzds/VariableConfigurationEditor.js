import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const StUFZDSVariableConfigurationEditor = ({variable, component = undefined}) => {
  if (component?.type !== 'file') {
    throw new Error('Only file components are supported');
  }
  return (
    <Fieldset>
      <Title componentKey={component.key} />
    </Fieldset>
  );
};

const Title = ({componentKey}) => {
  // the formik state is populated with the backend options, so our path needs to be
  // relative to that
  const [props] = useField(`files['${componentKey}'].title`);
  return (
    <FormRow>
      <Field
        name={props.name}
        label={
          <FormattedMessage
            description="Document upload: title option label"
            defaultMessage="Title"
          />
        }
        helpText={
          <FormattedMessage
            description="Document upload: title option help text"
            defaultMessage={`Optional custom title for the document. By default, the
            file name is used.`}
          />
        }
      >
        <TextInput {...props} maxLength="200" value={props.value ?? ''} />
      </Field>
    </FormRow>
  );
};

export default StUFZDSVariableConfigurationEditor;
