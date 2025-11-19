import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const ProfileFormVariable = ({name = 'profileFormVariable'}) => {
  const [fieldProps] = useField(name);
  return (
    <FormRow>
      <Field
        name={name}
        label={
          <FormattedMessage
            description="Profile form variable label"
            defaultMessage="Profile form variable"
          />
        }
        required
        noManageChildProps
      >
        <VariableSelection
          {...fieldProps}
          aria-label={
            <FormattedMessage
              description="Accessible label for (form) variable dropdown"
              defaultMessage="Profile form variable dropdown"
            />
          }
          filter={variable => variable.source === 'component'}
        />
      </Field>
    </FormRow>
  );
};

ProfileFormVariable.propTypes = {
  /**
   * Name to use for the form field, is passed down to Formik.
   */
  name: PropTypes.string,
};

export default ProfileFormVariable;
