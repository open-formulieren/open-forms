import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const CustomerInteractionsAPIGroup = ({apiGroupChoices, name}) => {
  const options = apiGroupChoices.map(([value, label]) => ({value, label}));

  return (
    <FormRow>
      <Field
        name={name}
        required
        label={
          <FormattedMessage
            description="Customer interactions API group field label"
            defaultMessage="API group"
          />
        }
        helpText={
          <FormattedMessage
            description="Customer interactions API group field help text"
            defaultMessage="The API group specifies which Customer interactions service to use."
          />
        }
        noManageChildProps
      >
        <ReactSelect name={name} options={options} required />
      </Field>
    </FormRow>
  );
};

CustomerInteractionsAPIGroup.propTypes = {
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.string, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,

  /**
   * Name to use for the form field, is passed down to Formik.
   */
  name: PropTypes.string.isRequired,
};

export default CustomerInteractionsAPIGroup;
