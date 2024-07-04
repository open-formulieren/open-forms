import PropTypes from 'prop-types';
import React, {useEffect} from 'react';

import ReactSelect from 'components/admin/forms/ReactSelect';

const ObjectTypeSelect = ({availableObjectTypesState, objecttype, onChange}) => {
  const {loading, availableObjecttypes, error} = availableObjectTypesState;

  const options =
    loading || error
      ? []
      : availableObjecttypes.map(({uuid, name, dataClassification}) => {
          return {value: uuid, label: `${name} (${dataClassification})`};
        });

  // ensure that if no valid value is present, the first possible option is set (
  // synchronize the UI state back to the form state)
  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || !availableObjecttypes.length) return;

    // check if a valid option is selected, if this is the case -> do nothing
    const isOptionPresent = availableObjecttypes.find(ot => ot.uuid === objecttype);
    if (isOptionPresent) return;

    // otherwise select the first possible option and persist that back into the state
    const fakeEvent = {target: {name: 'objecttype', value: availableObjecttypes[0].uuid}};
    onChange(fakeEvent);
  });

  return (
    <ReactSelect
      name="objecttype"
      value={objecttype}
      options={options}
      onChange={onChange}
      isClearable={false}
      emptyValue=""
    />
  );
};

ObjectTypeSelect.propTypes = {
  availableObjectTypesState: PropTypes.object.isRequired,
  objecttype: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default ObjectTypeSelect;
