import {useField} from 'formik';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import ActionButton from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const Variables = () => {
  const intl = useIntl();

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
            defaultMessage="Variables to include in the data to be sent."
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

          <ActionButton
            name="addAllFormVariables"
            type="button"
            text={intl.formatMessage({
              description: "JSON registration options 'add all form variables' label",
              defaultMessage: 'Add all form variables',
            })}
            onClick={() => {
              const componentVariables = formVariables.filter(
                v => v.source === VARIABLE_SOURCES.component
              );
              const newVariables = [...fieldProps.value, ...componentVariables.map(v => v.key)];
              setValue([...new Set(newVariables)]); // Use a Set to ensure they are unique
            }}
          />
        </div>
      </Field>
    </FormRow>
  );
};

export default Variables;
