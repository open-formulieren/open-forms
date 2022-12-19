import PropTypes from 'prop-types';
import React from 'react';

const ChangelistColumn = ({objProp, isBool = false, children}) => {
  // don't actually render anything - this column is just used for the higher order component
  return null;
};

ChangelistColumn.tableRole = 'column';

ChangelistColumn.propTypes = {
  objProp: PropTypes.string.isRequired,
  isBool: PropTypes.bool,
  children: PropTypes.node,
};

export default ChangelistColumn;
