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
  htmlId,
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

  // Auto-select if only one available:
  useEffect(() => {
    if (loading || availableVersions.length !== 1) return;

    const fakeEvent = {target: {name: 'objecttypeVersion', value: availableVersions[0].version}};
    onChange(fakeEvent);
  }, [loading, availableVersions]);

  return (
    <ReactSelect
      name="objecttypeVersion"
      value={selectedVersion}
      options={options}
      htmlId={htmlId}
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
