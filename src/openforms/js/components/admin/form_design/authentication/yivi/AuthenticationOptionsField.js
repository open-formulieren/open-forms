import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

const AuthenticationOptionsField = ({schema}) => {
  const authenticationOptionsOptions = getReactSelectOptionsFromSchema(
    schema.properties.authenticationOptions.items.enum,
    schema.properties.authenticationOptions.items.enumNames
  );
  return (
    <FormRow>
      <Field
        name="authenticationOptions"
        label={
          <FormattedMessage
            description="Authentication options label"
            defaultMessage="Authentication options"
          />
        }
        helpText={
          <FormattedMessage
            description="Authentication options help text"
            defaultMessage="Specify which authentication options are available for users. If left empty, a pseudonym will be used as identifier."
          />
        }
      >
        <ReactSelect name="authenticationOptions" options={authenticationOptionsOptions} isMulti />
      </Field>
    </FormRow>
  );
};

AuthenticationOptionsField.propType = {
  schema: PropTypes.exact({
    type: PropTypes.oneOf(['object']).isRequired,
    properties: PropTypes.shape({
      authenticationOptions: PropTypes.exact({
        type: PropTypes.oneOf(['array']).isRequired,
        title: PropTypes.string.isRequired,
        description: PropTypes.string.isRequired,
        items: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }),
      }).isRequired,
    }),
  }).isRequired,
};

export default AuthenticationOptionsField;
