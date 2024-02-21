import React, {useEffect} from 'react';
import useAsync from 'react-use/esm/useAsync';

import Select from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

// TODO: properly translate this
const LOADING_OPTION = [['...', 'loading...']];

const getObjecttypeVersionsEndpoint = objecttype => {
  const bits = [
    '/api/v2/registration/plugins/objects-api/object-types',
    encodeURIComponent(objecttype.uuid),
    'versions',
  ];
  return bits.join('/');
};

const ObjectTypeVersionSelect = ({
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
    const objecttype = availableObjecttypes.find(ot => ot.url == selectedObjecttype);
    // no match -> no versions to retrieve;
    if (!objecttype) return [];

    const response = await get(getObjecttypeVersionsEndpoint(objecttype));
    if (!response.ok) {
      throw new Error('Loading available object types failed');
    }
    const versions = response.data;
    return versions.sort((v1, v2) => v2.version - v1.version);
  }, [selectedObjecttype, objecttypeUrls]);

  const choices =
    loading || error
      ? LOADING_OPTION
      : availableVersions.map(version => [
          version.version,
          `${version.version} (${version.status})`,
        ]);

  // ensure that if no valid value is present, the first possible option is set (
  // synchronize the UI state back to the form state)
  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || availableVersions.length == 0) return;

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
    <>
      <Select
        id="root_objecttypeVersion"
        name="objecttypeVersion"
        choices={choices}
        value={selectedVersion ?? ''}
        onChange={onChange}
      />
    </>
  );
};

export default ObjectTypeVersionSelect;
