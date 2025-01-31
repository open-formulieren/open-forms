import {useField} from 'formik';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const Variables = () => {
  const [fieldProps, , {setValue}] = useField('variables');

  const {formVariables} = useContext(FormContext);

  return (
    <FormRow>
      <Field
        name="variables"
        label={
          <FormattedMessage
            description="JSON registration options 'variables' label"
            defaultMessage="Variables"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'variables' helpText"
            defaultMessage="Which variables to include in the data to be sent"
          />
        }
        required
        noManageChildProps
      >
        <div className="json-dump-variables json-dump-variables--horizontal">
          <VariableSelection
            {...fieldProps}
            isMulti
            required
            closeMenuOnSelect={false}
            includeStaticVariables
          />

          <button
            type="button"
            className="button button--padded"
            onClick={() => onAddAllComponentVariables(formVariables, setValue)}
          >
            <FormattedMessage
              description="JSON registration options 'add all form variables' label"
              defaultMessage="Add all form variables"
            />
          </button>
        </div>
      </Field>
    </FormRow>
  );
};

function onAddAllComponentVariables(formVariables, setValue) {
  const componentVariables = formVariables.filter(v => v.source === VARIABLE_SOURCES.component);
  setValue(componentVariables.map(v => v.key));
}

export default Variables;
