import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextArea} from 'components/admin/forms/Inputs';

const CaseExplanation = () => {
  const [fieldProps] = useField('zaakToelichting');
  return (
    <FormRow>
      <Field
        name="zaakToelichting"
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'zaakToelichting' label"
            defaultMessage="Case explanation"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'zaakToelichting' help text"
            defaultMessage={`Explanation of the case. You can use the expressions like
            '{{ form_name }}' or other variables here.`}
          />
        }
      >
        <TextArea id="id_zaakToelichting" rows={2} cols={85} {...fieldProps} />
      </Field>
    </FormRow>
  );
};

CaseExplanation.propTypes = {};

export default CaseExplanation;
