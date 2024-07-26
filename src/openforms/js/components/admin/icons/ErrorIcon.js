import PropTypes from 'prop-types';
import React from 'react';

import FAIcon from './FAIcon';

const ErrorIcon = ({text, extraClassname}) => (
  <FAIcon icon="exclamation-circle" extraClassname={extraClassname} accessibleLabel={text} />
);

ErrorIcon.propTypes = {
  text: PropTypes.string,
  extraClassname: PropTypes.string,
};

export default ErrorIcon;
