import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const UpdateExistingObject = () => {
  const [fieldProps] = useField({name: 'updateExistingObject', type: 'checkbox'});

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
