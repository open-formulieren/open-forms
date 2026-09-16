import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const UseEmptyStringForEmptyDatelikeVariables = () => {
  const [fieldProps] = useField({
    name: 'useEmptyStringForEmptyDatelikeVariables',
    type: 'checkbox',
  });

  return (
    <FormRow>
      <Checkbox
        id="id_useEmptyStringForEmptyDatelikeVariables"
        label={
          <FormattedMessage
            description="Objects API registration options 'useEmptyStringForEmptyDatelikeVariables' label"
            defaultMessage="Use empty string for empty date, datetime and time values"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration options 'useEmptyStringForEmptyDatelikeVariables' helpText"
            defaultMessage={`Legacy compatibility option - send empty values for date, datetime and
              time components as empty string instead of <code>null</code>. This option will be
              removed in Open Forms 5.0.
            `}
            values={{
              code: chunks => <code>{chunks}</code>,
            }}
          />
        }
        {...fieldProps}
      />
    </FormRow>
  );
};

UseEmptyStringForEmptyDatelikeVariables.propTypes = {};

export default UseEmptyStringForEmptyDatelikeVariables;
