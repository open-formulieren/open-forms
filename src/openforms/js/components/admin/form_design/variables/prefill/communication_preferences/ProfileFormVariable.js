import {useField} from 'formik';
import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const ProfileFormVariable = ({name}) => {
  const {components} = useContext(FormContext);
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
          filter={variable =>
            variable.source === 'component' && components[variable.key]?.type === 'customerProfile'
          }
        />
      </Field>
    </FormRow>
  );
};

ProfileFormVariable.propTypes = {
  /**
   * Name to use for the form field, is passed down to Formik.
   */
  name: PropTypes.string.isRequired,
};

export default ProfileFormVariable;
