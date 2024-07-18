import PropTypes from 'prop-types';
import React from 'react';

import ReactSelect from 'components/admin/forms/ReactSelect';

const InformatieObjecttypeSelect = ({
  name,
  htmlId,
  availableInformatieObjecttypenState,
  informatieObjecttype,
  onChange,
  isClearable = true,
}) => {
  const {loading, availableInformatieobjecttypen, error} = availableInformatieObjecttypenState;

  const options =
    loading || error
      ? []
      : availableInformatieobjecttypen.map(({omschrijving}) => {
          return {value: omschrijving, label: omschrijving};
        });

  return (
    <ReactSelect
      name={name}
      value={informatieObjecttype}
      options={options}
      htmlId={htmlId}
      onChange={onChange}
      emptyValue=""
      isClearable={isClearable}
    />
  );
};

InformatieObjecttypeSelect.propTypes = {
  name: PropTypes.string.isRequired,
  availableInformatieObjecttypenState: PropTypes.object.isRequired,
  informatieObjecttype: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  isClearable: PropTypes.bool,
};

export default InformatieObjecttypeSelect;
