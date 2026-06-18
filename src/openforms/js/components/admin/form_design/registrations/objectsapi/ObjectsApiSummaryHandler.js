import {FormattedMessage} from 'react-intl';

/**
 * Returns the Objects API Registration summary for a specific variable.
 *
 * Primarly intended for the v2 registration, but v1 *does* support editing file
 * components too.
 */
const ObjectsApiSummaryHandler = ({variable, backendOptions}) => {
  const {version = 2} = backendOptions;

  switch (version) {
    case 1: {
      return <ObjectsApiV1SummaryHandler variable={variable} backendOptions={backendOptions} />;
    }
    case 2: {
      return <ObjectsApiV2SummaryHandler variable={variable} backendOptions={backendOptions} />;
    }
    default: {
      throw new Error(`Unknown options version '${version}'.`);
    }
  }
};

/**
 * Returns the Objects API Registration summary for a specific variable, scoped to the
 * v1 registration options, supporting only file components.
 *
 * @typedef {{
 *   files: {
 *     key: string;
 *     documentTypeDescription: string,
 *     organizationRsin: string,
 *     confidentialityLevel: string,
 *     title: string,
 *   }[],
 * }} ObjectsAPIV1Options
 *
 * @param {Object} p
 * @param {string} p.variable - The current variable
 * @param {ObjectsAPIV1Options} p.backendOptions - The Objects API Options (guaranteed to be v2)
 * @returns {JSX.Element} - The summary, represented as the parts of the target path separated by '>'
 */
const ObjectsApiV1SummaryHandler = ({variable, backendOptions}) => {
  const documentType = backendOptions?.files?.find(
    opts => opts.key === variable.key
  )?.documentTypeDescription;
  if (documentType) {
    return (
      <FormattedMessage
        description="'Document type override' registration summary message"
        defaultMessage="Document type specified"
      />
    );
  }
  return null;
};

/**
 * Returns the Objects API Registration summary for a specific variable, scoped to the
 * v2 registration options
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
const ObjectsApiV2SummaryHandler = ({variable, backendOptions}) => {
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

  const variableMapping = backendOptions.variablesMapping?.find(
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
