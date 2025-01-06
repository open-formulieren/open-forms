import React from 'react';
import {FormattedMessage} from 'react-intl';

/**
 * Returns the Objects API Registration summary for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   variablesMapping: {variableKey: string, targetPath: string[]}[],
 *   geometryVariableKey: string,
 * }} ObjectsAPIV2Options
 *
 * @param {Object} p
 * @param {string} p.variable - The current variable
 * @param {ObjectsAPIV2Options} p.backendOptions - The Objects API Options (guaranteed to be v2)
 * @returns {JSX.Element} - The summary, represented as the parts of the target path separated by '>'
 */
const ObjectsApiSummaryHandler = ({variable, backendOptions}) => {
  const geometryVariableKey = backendOptions.geometryVariableKey;

  if (geometryVariableKey && geometryVariableKey === variable.key) {
    return (
      <FormattedMessage
        description="'Mapped to geometry' registration summary message"
        defaultMessage="Mapped to the {geometryPath} attribute"
        values={{geometryPath: <code>record.geometry</code>}}
      />
    );
  }

  const variableMapping = backendOptions.variablesMapping.find(
    mapping => mapping.variableKey === variable.key
  );

  if (
    !variableMapping ||
    (!variableMapping.targetPath &&
      variableMapping.options &&
      !Object.keys(variableMapping.options).length > 0)
  ) {
    return (
      <FormattedMessage
        description="'Not yet configured' registration summary message"
        defaultMessage="Not yet configured"
      />
    );
  }

  if (variableMapping.options && Object.keys(variableMapping.options).length > 0) {
    return (
      <FormattedMessage
        description="'Multiple target paths configured' registration summary message"
        defaultMessage="Multiple target paths configured"
      />
    );
  }

  return variableMapping.targetPath
    .map(p => <code>{p}</code>)
    .reduce((res, item) => (
      <>
        {res} &rsaquo; {item}
      </>
    ));
};

export default ObjectsApiSummaryHandler;
