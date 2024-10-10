import {useField} from 'formik';

import FormRow from 'components/admin/forms/FormRow';

import PaymentStatusUpdateMappingInputs from './inputs/PaymentStatusUpdateMappingInputs';

const PaymentStatusUpdateMapping = () => {
  const [fieldProps, , fieldHelpers] = useField('paymentStatusUpdateMapping');
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <PaymentStatusUpdateMappingInputs
        name="paymentStatusUpdateMapping"
        onChange={newValue => setValue(newValue)}
        values={fieldProps.value}
      />
    </FormRow>
  );
};

PaymentStatusUpdateMapping.propTypes = {};

export default PaymentStatusUpdateMapping;
