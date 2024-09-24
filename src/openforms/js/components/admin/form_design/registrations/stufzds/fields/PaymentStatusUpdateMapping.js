import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

import PaymentStatusUpdateMappingInputs from './inputs/PaymentStatusUpdateMappingInputs';

const PaymentStatusUpdateMapping = ({schema}) => {
  const [fieldProps, , fieldHelpers] = useField('paymentStatusUpdateMapping');
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <Field
        name="paymentStatusUpdateMapping"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'paymentStatusUpdateMapping' label"
            defaultMessage="payment status update variable mapping"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'paymentStatusUpdateMapping' helpText"
            defaultMessage="This mapping is used to map the variable keys to keys used in the XML that is sent to StUF-ZDS. Those keys and the values belonging to them in the submission data are included in extraElementen."
          />
        }
      >
        <PaymentStatusUpdateMappingInputs
          name="paymentStatusUpdateMapping"
          onChange={newValue => setValue(newValue)}
          values={fieldProps.value}
        />
      </Field>
    </FormRow>
  );
};

PaymentStatusUpdateMapping.propTypes = {
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};

export default PaymentStatusUpdateMapping;
