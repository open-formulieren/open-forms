import PropTypes from 'prop-types';
import React, {useEffect} from 'react';
import useAsync from 'react-use/esm/useAsync';

import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

const getObjecttypeVersionsEndpoint = objecttype => {
  const bits = [
    '/api/v2/registration/plugins/objects-api/object-types',
    encodeURIComponent(objecttype.uuid),
    'versions',
  ];
  return bits.join('/');
};

const ObjectTypeVersionSelect = ({
  objectsApiGroup,
  availableObjecttypes = [],
  selectedObjecttype,
  selectedVersion,
  onChange,
}) => {
  const objecttypeUrls = JSON.stringify(availableObjecttypes.map(ot => ot.url).sort());

  const {
    loading,
    value: availableVersions = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    const objecttype = availableObjecttypes.find(ot => ot.uuid === selectedObjecttype);
    // no match -> no versions to retrieve;
    if (!objecttype) return [];

    const params = {objects_api_group: objectsApiGroup};
    const response = await get(getObjecttypeVersionsEndpoint(objecttype), params);
    if (!response.ok) {
      throw new Error('Loading available object types failed');
    }
    const versions = response.data;
    return versions.sort((v1, v2) => v2.version - v1.version);
  }, [selectedObjecttype, objecttypeUrls, objectsApiGroup]);

  const options =
    loading || error
      ? []
      : availableVersions.map(version => {
          return {value: version.version, label: `${version.version} (${version.status})`};
        });

  // ensure that if no valid value is present, the first possible option is set (
  // synchronize the UI state back to the form state)
  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || availableVersions.length === 0) return;

    // check if a valid option is selected, if this is the case -> do nothing
    const isOptionPresent = availableVersions.find(
      version => parseInt(version.version) === parseInt(selectedVersion)
    );
    if (isOptionPresent) return;

    // otherwise select the first possible option and persist that back into the state
    const fakeEvent = {target: {name: 'objecttypeVersion', value: availableVersions[0].version}};
    onChange(fakeEvent);
  });

  return (
    <ReactSelect
      name="objecttypeVersion"
      value={selectedVersion}
      options={options}
      onChange={onChange}
      isClearable={false}
      emptyValue=""
    />
  );
};

ObjectTypeVersionSelect.propTypes = {
  objectsApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  availableObjecttypes: PropTypes.array,
  selectedObjecttype: PropTypes.string.isRequired,
  selectedVersion: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default ObjectTypeVersionSelect;
