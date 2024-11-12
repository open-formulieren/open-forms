import {useField} from 'formik';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FeatureFlagsContext} from 'components/admin/form_design/Context';
import ArrayInput from 'components/admin/forms/ArrayInput';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

const AuthAttributePath = () => {
  const [fieldProps, , fieldHelpers] = useField({name: 'authAttributePath', type: 'array'});
  const [updateExistingObject] = useField('updateExistingObject');
  const {setValue} = fieldHelpers;
  const {REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION = false} =
    useContext(FeatureFlagsContext);

  if (!REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION) {
    return null;
  }

  return (
    <FormRow>
      <Field
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
        required={!!updateExistingObject.value}
      >
        <ArrayInput
          name="authAttributePath"
          values={fieldProps.value}
          onChange={value => {
            setValue(value);
          }}
          inputType="text"
        />
      </Field>
    </FormRow>
  );
};

AuthAttributePath.propTypes = {};

export default AuthAttributePath;
