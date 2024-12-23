import {FormattedMessage} from 'react-intl';
import React from 'react';

const JSONSummaryHandler = ({variable, backendOptions}) => {

  const isIncluded = backendOptions.formVariables.includes(variable.key);

  if (isIncluded) {
    return (
      <FormattedMessage
        description="JSON registration summary message"
        defaultMessage="Included"
      />
    );
  }
  else {
    return (
      <FormattedMessage
        description="JSON registration summary message"
        defaultMessage="Not included"
      />
    );
  }
};


// TODO-4098: ??
JSONSummaryHandler.propTypes = {

};

export default JSONSummaryHandler;
