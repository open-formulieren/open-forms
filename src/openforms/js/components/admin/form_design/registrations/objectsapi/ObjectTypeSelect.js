import PropTypes from 'prop-types';
import React, {useEffect} from 'react';

import Select, {LOADING_OPTION} from 'components/admin/forms/Select';

const ObjectTypeSelect = ({availableObjectTypesState, objecttype, onChange}) => {
  const {loading, availableObjecttypes, error} = availableObjectTypesState;

  const choices =
    loading || error
      ? LOADING_OPTION
      : availableObjecttypes.map(({url, name, dataClassification}) => [
          url,
          `${name} (${dataClassification})`,
        ]);

  // ensure that if no valid value is present, the first possible option is set (
  // synchronize the UI state back to the form state)
  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || !availableObjecttypes.length) return;

    // check if a valid option is selected, if this is the case -> do nothing
    const isOptionPresent = availableObjecttypes.find(ot => ot.url === objecttype);
    if (isOptionPresent) return;

    // otherwise select the first possible option and persist that back into the state
    const fakeEvent = {target: {name: 'objecttype', value: availableObjecttypes[0].url}};
    onChange(fakeEvent);
  });

  useEffect(() => {
    if (loading) return;
    onChange({target: {name: 'objecttypeVersion', value: ''}});
  }, [objecttype]);

  return (
    <Select
      id="root_objecttype"
      name="objecttype"
      choices={choices}
      value={objecttype}
      onChange={onChange}
    />
  );
};

ObjectTypeSelect.propTypes = {
  availableObjectTypesState: PropTypes.object.isRequired,
  objecttype: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default ObjectTypeSelect;
