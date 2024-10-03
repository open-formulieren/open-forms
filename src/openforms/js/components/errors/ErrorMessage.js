import PropTypes from 'prop-types';
import React from 'react';

import {ErrorIcon} from 'components/admin/icons';

const ErrorMessage = ({children}) => {
  if (!children) return null;
  return (
    <div className="error-message" role="alert">
      <span className="error-message__icon icon icon--danger icon--as-lead">
        <ErrorIcon text="error" />
      </span>
      <div className="error-message__children">{children}</div>
    </div>
  );
};

ErrorMessage.propTypes = {
  children: PropTypes.node,
};

export default ErrorMessage;
