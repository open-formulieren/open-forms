import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, defineMessages} from 'react-intl';

import Field from 'components/admin/forms/Field';
import {Checkbox} from 'components/admin/forms/Inputs';

export const FIELD_LABELS = defineMessages({
  product: {
    description: 'Label for additionalFormConfiguration product input',
    defaultMessage: 'Product',
  },
  wmsTileLayers: {
    description: 'Label for additionalFormConfiguration wmsTileLayers input',
    defaultMessage: 'WMS tile layers',
  },
  wmtsTileLayers: {
    description: 'Label for additionalFormConfiguration wmtsTileLayers input',
    defaultMessage: 'WMTS tile layers',
  },
  yiviAttributeGroups: {
    description: 'Label for additionalFormConfiguration yiviAttributeGroups input',
    defaultMessage: 'Yivi attribute groups',
  },
  theme: {
    description: 'Label for additionalFormConfiguration theme input',
    defaultMessage: 'Theme',
  },
  category: {
    description: 'Label for additionalFormConfiguration category input',
    defaultMessage: 'Category',
  },
});

const AdditionalFormConfigurationField = ({selectedAdditionalFormConfiguration, onChange}) => {
  const options = [
    'product',
    'wmsTileLayers',
    'wmtsTileLayers',
    'yiviAttributeGroups',
    'theme',
    'category',
  ];

  return (
    <Field
      name="additionalFormConfiguration"
      label={
        <FormattedMessage
          defaultMessage="Additional form configuration"
          description="Form import/export options 'additionalFormConfiguration' field label"
        />
      }
      helpText={
        <FormattedMessage
          defaultMessage="Which additional form configuration should be included in the export file content."
          description="Form import/export options 'additionalFormConfiguration' field help text"
        />
      }
    >
      <ul>
        {options.map(option => (
          <li key={option}>
            <Checkbox
              name={option}
              value={option}
              label={
                option in FIELD_LABELS ? <FormattedMessage {...FIELD_LABELS[option]} /> : option
              }
              onChange={onChange}
              checked={selectedAdditionalFormConfiguration.includes(option)}
              noVCheckbox
            />
          </li>
        ))}
      </ul>
    </Field>
  );
};

AdditionalFormConfigurationField.prototype = {
  onChange: PropTypes.func,
  selectedAdditionalFormConfiguration: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default AdditionalFormConfigurationField;
