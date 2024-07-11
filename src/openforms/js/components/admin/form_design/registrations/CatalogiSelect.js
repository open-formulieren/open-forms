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

  // ensure that if no valid value is present, the first possible option is set (
  // synchronize the UI state back to the form state)
  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || !availableCatalogi.length) return;

    // check if a valid option is selected, if this is the case -> do nothing
    const isOptionPresent = availableCatalogi.find(
      catalog => catalog.domein === catalogusDomein && catalog.rsin === catalogusRsin
    );
    if (isOptionPresent) return;

    // otherwise select the first possible option and persist that back into the state
    onChange(
      produce(formData, draft => {
        draft.catalogusDomein = availableCatalogi[0].domein;
        draft.catalogusRsin = availableCatalogi[0].rsin;
      })
    );
  }, []);

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
