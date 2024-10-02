import {useField} from 'formik';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FeatureFlagsContext} from 'components/admin/form_design/Context';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const UpdateExistingObject = () => {
  const [fieldProps] = useField({name: 'updateExistingObject', type: 'checkbox'});
  const {REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION = false} =
    useContext(FeatureFlagsContext);

  if (!REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION) {
    return null;
  }

  return (
    <FormRow>
      <Checkbox
        id="id_updateExistingObject"
        label={
          <FormattedMessage
            description="Objects API registration: updateExistingObject label"
            defaultMessage="Update existing object"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration: updateExistingObject helpText"
            defaultMessage="Indicates whether the existing object (retrieved from an optional initial data reference) should be updated, instead of creating a new one. If no existing object exists, a new one will be created instead."
          />
        }
        {...fieldProps}
      />
    </FormRow>
  );
};

UpdateExistingObject.propTypes = {};

export default UpdateExistingObject;
