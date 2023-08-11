import PropTypes from 'prop-types';
import React, {useContext} from 'react';

import Select from 'components/admin/forms/Select';

import {FormContext} from './Context';

const RegistrationBackendSelection = ({name, value, onChange}) => {
  const {registrationBackends = []} = useContext(FormContext);
  const registrationBackendChoices = registrationBackends.map(({key, name}) => [key, name]);

  return (
    <Select
      name={name}
      choices={registrationBackendChoices}
      allowBlank
      onChange={onChange}
      value={value}
    />
  );
};

RegistrationBackendSelection.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func,
};

export default RegistrationBackendSelection;
export {RegistrationBackendSelection};
