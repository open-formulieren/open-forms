import PropTypes from 'prop-types';
import React from 'react';

import FAIcon from 'components/admin/FAIcon';

const ErrorMessage = ({children}) => {
  if (!children) return null;
  return (
    <div className="error-message">
      <span className="error-message__icon icon icon--danger icon--as-lead">
        <FAIcon icon="exclamation-circle" title="error" />
      </span>
      <div className="error-message__children">{children}</div>
    </div>
  );
};

ErrorMessage.propTypes = {
  children: PropTypes.node,
  modifiers: PropTypes.arrayOf(PropTypes.string),
};

export default ErrorMessage;
