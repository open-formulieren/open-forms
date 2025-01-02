import {FormattedMessage} from 'react-intl';
import React from 'react';

const JSONSummaryHandler = ({variable, backendOptions}) => {
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


JSONSummaryHandler.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
  backendOptions: PropTypes.shape({
    formVariables: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
};

export default JSONSummaryHandler;
