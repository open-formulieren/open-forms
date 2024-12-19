import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const ServiceSelect = ({options}) => {
  return (
    <FormRow>
      <Field
        name="service"
        label={
          <FormattedMessage
            description="JSON registration options 'serviceSelect' label"
            defaultMessage="Service"
          />
        }
      >
        <ReactSelect
          name="service"
          options={options}
          required
        />
      </Field>
    </FormRow>
  );
};

ServiceSelect.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export default ServiceSelect;
