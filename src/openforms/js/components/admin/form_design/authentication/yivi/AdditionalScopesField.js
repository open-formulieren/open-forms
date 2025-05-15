import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

const AdditionalScopeSelectorOption = props => {
  const {value, label} = props.data;
  return (
    <components.Option {...props}>
      <span className="form-additional-scopes-dropdown-option">
        <span className="form-additional-scopes-dropdown-option__label">{label}</span>
        <code className="form-additional-scopes-dropdown-option__key">{value}</code>
      </span>
    </components.Option>
  );
};

const AdditionalScopeSelectorValueLabel = props => {
  const {value} = props.data;
  return <components.MultiValueLabel {...props}>{value}</components.MultiValueLabel>;
};

const AdditionalScopesField = ({schema}) => {
  const additionalScopesOptions = getReactSelectOptionsFromSchema(
    schema.properties.additionalScopes.items.enum,
    schema.properties.additionalScopes.items.enumNames
  );
  return (
    <FormRow>
      <Field
        name="additionalScopes"
        label={
          <FormattedMessage
            description="Additional scopes label"
            defaultMessage="Additional scopes"
          />
        }
        helpText={
          <FormattedMessage
            description="Additional scopes help text"
            defaultMessage="Additional scopes are used to request additional information from the user, which will become available as variables after login."
          />
        }
      >
        <ReactSelect
          name="additionalScopes"
          options={additionalScopesOptions}
          components={{
            Option: AdditionalScopeSelectorOption,
            MultiValueLabel: AdditionalScopeSelectorValueLabel,
          }}
          isMulti
          isClearable
        />
      </Field>
    </FormRow>
  );
};

AdditionalScopesField.propType = {
  schema: PropTypes.exact({
    type: PropTypes.oneOf(['object']).isRequired,
    properties: PropTypes.shape({
      additionalScopes: PropTypes.exact({
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

export default AdditionalScopesField;
