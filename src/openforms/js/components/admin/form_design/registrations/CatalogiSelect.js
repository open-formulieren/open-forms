import PropTypes from 'prop-types';
import React, {useEffect} from 'react';

import ReactSelect from 'components/admin/forms/ReactSelect';

const CatalogiSelect = ({
  name,
  htmlId,
  availableCatalogiState,
  catalogusDomein,
  catalogusRsin,
  onChange,
  isClearable = true,
}) => {
  const {loading, availableCatalogi, error} = availableCatalogiState;

  const onCatalogChange = event => {
    const {value} = event.target;
    if (value === '') {
      onChange({catalogusDomein: '', catalogusRsin: ''});
    } else {
      const splitValue = value.split('-');
      onChange({catalogusDomein: splitValue[0], catalogusRsin: splitValue[1]});
    }
  };

  const options =
    loading || error
      ? []
      : availableCatalogi.map(({domein, rsin}) => {
          return {value: `${domein}-${rsin}`, label: `${domein} (RSIN: ${rsin})`};
        });

  // const options =
  // loading || error
  //   ? []
  //   : availableCatalogi.map(({domein, rsin}) => {
  //       return {domein, rsin, label: `${domein} (RSIN: ${rsin})`};
  //     });

  return (
    <ReactSelect
      name={name}
      value={`${catalogusDomein}-${catalogusRsin}`}
      options={options}
      htmlId={htmlId}
      onChange={onCatalogChange}
      emptyValue=""
      isClearable={isClearable}
    />
  );
};

CatalogiSelect.propTypes = {
  name: PropTypes.string.isRequired,
  availableCatalogiState: PropTypes.object.isRequired,
  catalogusDomein: PropTypes.string.isRequired,
  catalogusRsin: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  isClearable: PropTypes.bool,
};

export default CatalogiSelect;
