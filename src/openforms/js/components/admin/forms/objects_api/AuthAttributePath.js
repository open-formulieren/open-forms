import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import ArrayInput from 'components/admin/forms/ArrayInput';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

const AuthAttributePath = ({name, required = true, ...extraProps}) => {
  const [fieldProps, , fieldHelpers] = useField({name: name, type: 'array'});
  const {setValue} = fieldHelpers;

  return (
    <FormRow>
      <Field
        name={name}
        label={
          <FormattedMessage
            description="Objects API registration: authAttributePath label"
            defaultMessage="Path to auth attribute (e.g. BSN/KVK) in objects"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration: authAttributePath helpText"
            defaultMessage="This is used to perform validation to verify that the authenticated user is the owner of the object."
          />
        }
        required={required}
      >
        <ArrayInput
          name={name}
          values={fieldProps.value}
          onChange={value => {
            setValue(value);
          }}
          inputType="text"
          {...extraProps}
        />
      </Field>
    </FormRow>
  );
};

AuthAttributePath.propTypes = {
  name: PropTypes.string.isRequired,
  required: PropTypes.bool,
};

export default AuthAttributePath;
