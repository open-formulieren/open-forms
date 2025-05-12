import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {SelectWithoutFormik} from 'components/admin/forms/ReactSelect';

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

const AdditionalScopesField = ({name, schema, additionalScopes, onChange, ...props}) => {
  const {enum: enumValue, enumNames} = schema.properties.additionalScopes.items;
  const additionalScopesOptions = enumValue.map((value, index) => ({
    label: enumNames[index],
    value,
  }));
  return (
    <FormRow>
      <Field
        name={name}
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
        <SelectWithoutFormik
          name={name}
          onChange={newValue => onChange({target: {name, value: newValue}})}
          options={additionalScopesOptions}
          value={additionalScopes}
          components={{
            Option: AdditionalScopeSelectorOption,
            MultiValueLabel: AdditionalScopeSelectorValueLabel,
          }}
          isMulti
          isClearable
          {...props}
        />
      </Field>
    </FormRow>
  );
};

AdditionalScopesField.propType = {
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  additionalScopes: PropTypes.arrayOf(PropTypes.string),
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
