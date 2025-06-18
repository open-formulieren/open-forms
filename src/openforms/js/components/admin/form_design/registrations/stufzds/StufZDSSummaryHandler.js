import {FormattedMessage} from 'react-intl';

/**
 * Returns the StUF-ZDS Registration summary for a specific variable.
 *
 * @param {Object} p
 * @param {string} p.variable - The current variable
 * @param {StufZDSOptions} p.backendOptions - The StUF-ZDS Options
 * @returns {JSX.Element} - The summary
 */
const StufZDSSummaryHandler = ({variable, backendOptions}) => {
  const variableMapping = backendOptions.variablesMapping.find(
    mapping => mapping.variableKey === variable.key
  );

  if (!variableMapping || !variableMapping.registerAs || !variableMapping.description) {
    return (
      <FormattedMessage
        description="'Not yet configured' registration summary message"
        defaultMessage="Not yet configured"
      />
    );
  }

  return (
    <code>
      <FormattedMessage
        defaultMessage="Registered as {type}"
        values={{type: variableMapping.registerAs}}
      />
    </code>
  );
};

export default StufZDSSummaryHandler;
