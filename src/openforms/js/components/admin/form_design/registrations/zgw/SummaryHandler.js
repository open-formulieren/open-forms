import {FormattedMessage} from 'react-intl';

/**
 * Returns the ZGW APIs Registration summary for a specific variable.
 *
 * Only supports file components!
 */
const ZGWSummaryHandler = ({component, backendOptions}) => {
  const documentType = backendOptions?.files?.[component.key]?.documentTypeDescription;
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

export default ZGWSummaryHandler;
