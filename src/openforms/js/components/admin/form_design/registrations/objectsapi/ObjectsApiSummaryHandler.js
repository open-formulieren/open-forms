import React from 'react';

const ObjectsApiSummaryHandler = ({variableKey, backendOptions}) => {
  const version = backendOptions.version;
  if (version !== 2) return null;

  const variableMapping = backendOptions.variablesMapping.find(
    mappings => mappings.variableKey === variableKey
  );
  if (!variableMapping) return null;

  return variableMapping.targetPath
    .map(p => <code>{p}</code>)
    .reduce((res, item) => (
      <>
        {res} &rsaquo; {item}
      </>
    ));
};

export default ObjectsApiSummaryHandler;
