import PropTypes from 'prop-types';
import React from 'react';
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
        helpText={
          <FormattedMessage
            description="JSON registration options 'serviceSelect' helpText"
            defaultMessage="The service to send the data to."
          />
        }
        required
        noManageChildProps
      >
        <ReactSelect name="service" options={options} required />
      </Field>
    </FormRow>
  );
};

ServiceSelect.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.number.isRequired,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export default ServiceSelect;
