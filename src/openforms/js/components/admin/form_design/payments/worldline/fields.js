import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

export const Merchant = ({options}) => (
  <FormRow>
    <Field
      name="merchant"
      label={
        <FormattedMessage
          description="Worldline payment options 'merchant' label"
          defaultMessage="Merchant"
        />
      }
      helpText={
        <FormattedMessage
          description="Worldline payment options 'merchant' help text"
          defaultMessage="Which merchant should be used for payments related to this form."
        />
      }
      required
    >
      <ReactSelect name="merchant" options={options} required />
    </Field>
  </FormRow>
);

Merchant.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.number,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};
