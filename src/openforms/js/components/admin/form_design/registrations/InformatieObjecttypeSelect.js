import PropTypes from 'prop-types';
import React, {useEffect} from 'react';

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

  let options;

  if (loading || error) {
    options = [];
  } else {
    const optionsMapping = availableInformatieobjecttypen.reduce((accumulator, temp) => {
      const {
        catalogus: {domein},
        informatieobjecttype: {omschrijving},
      } = temp;
      if (!accumulator[domein]) {
        accumulator[domein] = [];
      }

      accumulator[domein].push({value: omschrijving, label: omschrijving});
      return accumulator;
    }, {});

    options = Object.entries(optionsMapping).map(([groupLabel, options]) => ({
      label: groupLabel,
      options,
    }));
  }

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
