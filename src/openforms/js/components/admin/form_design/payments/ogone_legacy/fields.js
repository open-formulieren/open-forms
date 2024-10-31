import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

export const MerchantID = ({options}) => (
  <FormRow>
    <Field
      name="merchantId"
      label={
        <FormattedMessage
          description="Ogone legacy payment options 'merchantId' label"
          defaultMessage="Merchant ID"
        />
      }
      helpText={
        <FormattedMessage
          description="Ogone legacy payment options 'merchantId' help text"
          defaultMessage="Which merchant should be used for payments related to this form."
        />
      }
    >
      <ReactSelect name="merchantId" options={options} required />
    </Field>
  </FormRow>
);

MerchantID.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.bool,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};
