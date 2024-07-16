import PropTypes from 'prop-types';
import React, {useEffect} from 'react';

import ReactSelect from 'components/admin/forms/ReactSelect';

const ObjectTypeSelect = ({availableObjectTypesState, objecttype, onChange, htmlId}) => {
  const {loading, availableObjecttypes, error} = availableObjectTypesState;

  const options =
    loading || error
      ? []
      : availableObjecttypes.map(({uuid, name, dataClassification}) => {
          return {value: uuid, label: `${name} (${dataClassification})`};
        });

  // Auto-select if only one available:
  useEffect(() => {
    console.log(availableObjecttypes);
    if (loading || availableObjecttypes.length !== 1) return;

    const fakeEvent = {target: {name: 'objecttype', value: availableObjecttypes[0].uuid}};
    onChange(fakeEvent);
  }, [loading, availableObjecttypes]);

  return (
    <ReactSelect
      name="objecttype"
      value={objecttype}
      options={options}
      htmlId={htmlId}
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
