import PropTypes from 'prop-types';
import React from 'react';

import {IconNo, IconYes} from 'components/admin/BooleanIcons';

const JSONDumpSummaryHandler = ({variable, backendOptions}) => {
  const isIncluded = backendOptions.variables.includes(variable.key);

  return isIncluded ? <IconYes /> : <IconNo />;
};

JSONDumpSummaryHandler.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
  backendOptions: PropTypes.shape({
    variables: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
};

export default JSONDumpSummaryHandler;
