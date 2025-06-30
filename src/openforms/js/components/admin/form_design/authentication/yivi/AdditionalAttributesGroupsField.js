import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

const AdditionalGroupSelectorOption = props => {
  const {value, label} = props.data;
  return (
    <components.Option {...props}>
      <span className="form-additional-attributes-groups-dropdown-option">
        <b className="form-additional-attributes-groups-dropdown-option__key">{value}</b>
        <span className="form-additional-attributes-groups-dropdown-option__label">{label}</span>
      </span>
    </components.Option>
  );
};

const AdditionalGroupSelectorValueLabel = props => {
  const {value} = props.data;
  return <components.MultiValueLabel {...props}>{value}</components.MultiValueLabel>;
};

const AdditionalAttributesGroupsField = ({schema}) => {
  const additionalAttributesGroupsOptions = getReactSelectOptionsFromSchema(
    schema.properties.additionalAttributesGroups.items.enum,
    schema.properties.additionalAttributesGroups.items.enumNames
  );
  return (
    <FormRow>
      <Field
        name="additionalAttributesGroups"
        label={
          <FormattedMessage
            description="Additional attributes groups label"
            defaultMessage="Additional attributes groups"
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
          name="additionalAttributesGroups"
          options={additionalAttributesGroupsOptions}
          components={{
            Option: AdditionalGroupSelectorOption,
            MultiValueLabel: AdditionalGroupSelectorValueLabel,
          }}
          isMulti
          isClearable
        />
      </Field>
    </FormRow>
  );
};

AdditionalAttributesGroupsField.propType = {
  schema: PropTypes.exact({
    type: PropTypes.oneOf(['object']).isRequired,
    properties: PropTypes.shape({
      additionalAttributesGroups: PropTypes.exact({
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

export default AdditionalAttributesGroupsField;
