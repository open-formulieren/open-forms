import React from 'react';

/**
 * Returns the Objects API Registration summary for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   variablesMapping: {variableKey: string, targetPath: string[]}[]
 * }} ObjectsAPIV2Options
 *
 * @param {Object} p
 * @param {string} p.variableKey - The current variable key
 * @param {ObjectsAPIV2Options} p.backendOptions - The Objects API Options (guaranteed to be v2)
 * @returns {JSX.Element} - The summary, represented as a the parts of the target path separated by '>'
 */
const ObjectsApiSummaryHandler = ({variableKey, backendOptions}) => {
  // Guaranteed to exist:
  const variableMapping = backendOptions.variablesMapping.find(
    mapping => mapping.variableKey === variableKey
  );

  return variableMapping.targetPath
    .map(p => <code>{p}</code>)
    .reduce((res, item) => (
      <>
        {res} &rsaquo; {item}
      </>
    ));
};

export default ObjectsApiSummaryHandler;
