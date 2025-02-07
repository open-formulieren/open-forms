import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import {IconNo, IconYes} from 'components/admin/BooleanIcons';

const JSONDumpSummaryHandler = ({variable, backendOptions}) => {
  const isIncludedInVariables = backendOptions.variables?.includes(variable.key);
  const isIncludedInMetadata =
    backendOptions.fixedMetadataVariables?.includes(variable.key) ||
    backendOptions.additionalMetadataVariables?.includes(variable.key);

  return (
    <>
      <FormattedMessage
        description="Label indicating the 'values' part of the data"
        defaultMessage="Values: "
      />
      {isIncludedInVariables ? <IconYes /> : <IconNo />}
      &nbsp;
      <FormattedMessage
        description="Label indicating the 'metadata' part of the data"
        defaultMessage="Metadata:"
      />
      {isIncludedInMetadata ? <IconYes /> : <IconNo />}
    </>
  );
};

JSONDumpSummaryHandler.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
  backendOptions: PropTypes.shape({
    variables: PropTypes.arrayOf(PropTypes.string).isRequired,
    fixedMetadataVariables: PropTypes.arrayOf(PropTypes.string).isRequired,
    additionalMetadataVariables: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
};

export default JSONDumpSummaryHandler;
