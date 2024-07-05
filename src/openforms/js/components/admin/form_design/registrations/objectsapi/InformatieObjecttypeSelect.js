import PropTypes from 'prop-types';
import React, {useEffect} from 'react';

import ReactSelect from 'components/admin/forms/ReactSelect';

const InformatieObjecttypeSelect = ({
  name,
  htmlId,
  availableInformatieObjecttypenState,
  informatieObjecttype,
  onChange,
}) => {
  const {loading, availableInformatieobjecttypen, error} = availableInformatieObjecttypenState;

  let options;

  if (loading || error) {
    options = [];
  } else {
    const optionsMapping = availableInformatieobjecttypen.reduce((accumulator, temp) => {
      const {
        catalogus: {domein},
        informatieobjecttype: {url, omschrijving},
      } = temp;
      if (!accumulator[domein]) {
        accumulator[domein] = [];
      }

      accumulator[domein].push({value: url, label: omschrijving});
      return accumulator;
    }, {});

    options = Object.entries(optionsMapping).map(([groupLabel, options]) => ({
      label: groupLabel,
      options,
    }));
  }

  // ensure that if no valid value is present, the first possible option is set (
  // synchronize the UI state back to the form state)
  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || !availableInformatieobjecttypen.length) return;

    // check if a valid option is selected, if this is the case -> do nothing
    const isOptionPresent = availableInformatieobjecttypen.find(
      iot => iot.informatieobjecttype.url === informatieObjecttype
    );
    if (isOptionPresent) return;

    // otherwise select the first possible option and persist that back into the state
    const fakeEvent = {
      target: {name, value: availableInformatieobjecttypen[0].informatieobjecttype.url},
    };
    onChange(fakeEvent);
  }, []);

  return (
    <ReactSelect
      name={name}
      value={informatieObjecttype}
      options={options}
      htmlId={htmlId}
      onChange={onChange}
      emptyValue=""
    />
  );
};

InformatieObjecttypeSelect.propTypes = {
  name: PropTypes.string.isRequired,
  availableInformatieObjecttypenState: PropTypes.object.isRequired,
  informatieObjecttype: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default InformatieObjecttypeSelect;
