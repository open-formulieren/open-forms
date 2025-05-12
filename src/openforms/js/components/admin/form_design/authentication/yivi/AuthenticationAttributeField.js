import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

const AuthenticationAttributeField = ({name, schema, authenticationAttribute, onChange}) => {
  const {enum: enumValue, enumNames} = schema.properties.authenticationAttribute;
  const authenticationAttributeChoices = enumValue.map((value, index) => [value, enumNames[index]]);
  return (
    <FormRow>
      <Field
        name={name}
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
        <Select
          value={authenticationAttribute}
          onChange={onChange}
          choices={authenticationAttributeChoices}
        />
      </Field>
    </FormRow>
  );
};

AuthenticationAttributeField.propType = {
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  authenticationAttribute: PropTypes.string,
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
