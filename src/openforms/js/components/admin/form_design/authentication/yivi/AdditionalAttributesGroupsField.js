import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const AdditionalGroupSelectorOption = props => {
  const {label, description} = props.data;
  return (
    <components.Option {...props}>
      <span className="form-additional-attributes-groups-dropdown-option">
        <b className="form-additional-attributes-groups-dropdown-option__key">{label}</b>
        <span className="form-additional-attributes-groups-dropdown-option__label">
          {description}
        </span>
      </span>
    </components.Option>
  );
};

const AdditionalGroupSelectorValueLabel = props => {
  const {label} = props.data;
  return <components.MultiValueLabel {...props}>{label}</components.MultiValueLabel>;
};

const AdditionalAttributesGroupsField = () => {
  const {availableYiviAttributeGroups} = useContext(FormContext);
  const additionalAttributesGroupsOptions = availableYiviAttributeGroups.map(attributeGroup => ({
    value: attributeGroup.slug,
    label: attributeGroup.name,
    description: attributeGroup.description,
  }));

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
