import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

const AuthenticationAttributeField = ({schema}) => {
  const authenticationAttributeOptions = getReactSelectOptionsFromSchema(
    schema.properties.authenticationAttribute.enum,
    schema.properties.authenticationAttribute.enumNames
  );
  return (
    <FormRow>
      <Field
        name="authenticationAttribute"
        label={
          <FormattedMessage
            description="Authentication attribute label"
            defaultMessage="Authentication attribute"
          />
        }
        helpText={
          <FormattedMessage
            description="Authentication attribute help text"
            defaultMessage="Specify which authentication attribute should be received from the login."
          />
        }
      >
        <ReactSelect name="authenticationAttribute" options={authenticationAttributeOptions} />
      </Field>
    </FormRow>
  );
};

AuthenticationAttributeField.propType = {
  schema: PropTypes.exact({
    type: PropTypes.oneOf(['object']).isRequired,
    properties: PropTypes.shape({
      authenticationAttribute: PropTypes.exact({
        type: PropTypes.oneOf(['string']).isRequired,
        title: PropTypes.string.isRequired,
        description: PropTypes.string.isRequired,
        enum: PropTypes.arrayOf(PropTypes.string).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }),
  }).isRequired,
};

export default AuthenticationAttributeField;
