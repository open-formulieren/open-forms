import {useField} from 'formik';
import React from 'react';
import {FormattedMessage, defineMessages} from 'react-intl';

import Field from 'components/admin/forms/Field';
import {Checkbox} from 'components/admin/forms/Inputs';

import {useFormConfigurationOptions} from './useExportOptions';

export const FIELD_LABELS = defineMessages({
  registrationBackends: {
    description: 'Label for formConfiguration registrationBackends input',
    defaultMessage: 'Registration backends',
  },
  prefill: {
    description: 'Label for formConfiguration prefill input',
    defaultMessage: 'Prefill',
  },
  paymentBackend: {
    description: 'Label for formConfiguration paymentBackend input',
    defaultMessage: 'Payment provider',
  },
  authBackends: {
    description: 'Label for formConfiguration authBackends input',
    defaultMessage: 'Authentication backends',
  },
});

const FormConfigurationField = () => {
  const options = useFormConfigurationOptions();
  const [fieldProps, , fieldHelpers] = useField('formConfiguration');
  const {value: selected} = fieldProps;
  const {setValue} = fieldHelpers;

  return (
    <Field
      name="formConfiguration"
      label={
        <FormattedMessage
          defaultMessage="Form configuration"
          description="Form import/export options 'formConfiguration' field label"
        />
      }
      helpText={
        <FormattedMessage
          defaultMessage="Which form configuration should be included in the export file content."
          description="Form import/export options 'formConfiguration' field help text"
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
              checked={selected?.includes(option)}
              noVCheckbox
            />
          </li>
        ))}
      </ul>
    </Field>
  );
};

export default FormConfigurationField;
