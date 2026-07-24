import {useField} from 'formik';
import React from 'react';
import {FormattedMessage, defineMessages} from 'react-intl';

import Field from 'components/admin/forms/Field';
import {Checkbox} from 'components/admin/forms/Inputs';

import {useAdditionalFormConfigurationOptions} from './useExportOptions';

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

const AdditionalFormConfigurationField = () => {
  const options = useAdditionalFormConfigurationOptions();
  const [fieldProps, , fieldHelpers] = useField('additionalFormConfiguration');
  const {value: selected} = fieldProps;
  const {setValue} = fieldHelpers;

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
              onChange={() => {
                if (selected.includes(option)) {
                  setValue(selected.filter(value => value !== option));
                } else {
                  setValue([...selected, option]);
                }
              }}
              checked={selected.includes(option)}
              noVCheckbox
            />
          </li>
        ))}
      </ul>
    </Field>
  );
};

export default AdditionalFormConfigurationField;
