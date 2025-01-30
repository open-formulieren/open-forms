import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import {getVariableSource} from 'components/admin/form_design/variables/utils';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const MetadataVariables = () => {
  const [fieldProps] = useField('additionalMetadataVariables');
  const [, {value}] = useField('fixedMetadataVariables');

  return (
    <FormRow>
      <Field
        name="additionalMetadataVariables"
        label={
          <FormattedMessage
            description="JSON registration options 'additionalMetadataVariables' label"
            defaultMessage="Additional metadata variables"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'additionalMetadataVariables' helpText"
            defaultMessage="Which additional variables to include in the metadata (the following are already included by default: {alreadyIncluded})"
            values={{alreadyIncluded: value.join(', ')}}
          />
        }
        noManageChildProps
      >
        <VariableSelection
          {...fieldProps}
          isMulti
          closeMenuOnSelect={false}
          includeStaticVariables
          filter={variable =>
            getVariableSource(variable) === VARIABLE_SOURCES.static && !value.includes(variable.key)
          } // Only show static variables and variables which are not already required
        />
      </Field>
    </FormRow>
  );
};

export default MetadataVariables;
