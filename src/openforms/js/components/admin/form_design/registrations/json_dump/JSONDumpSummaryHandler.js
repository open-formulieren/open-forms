import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

const JSONDumpSummaryHandler = ({variable, backendOptions}) => {
  const isIncluded = backendOptions.formVariables.includes(variable.key);

  if (isIncluded) {
    return (
      <FormattedMessage description="JSON registration summary message" defaultMessage="Included" />
    );
  } else {
    return (
      <FormattedMessage
        description="JSON registration summary message"
        defaultMessage="Not included"
      />
    );
  }
};

JSONDumpSummaryHandler.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
  backendOptions: PropTypes.shape({
    formVariables: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
};

export default JSONDumpSummaryHandler;
