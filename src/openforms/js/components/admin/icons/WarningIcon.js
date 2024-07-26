import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';

import FAIcon from './FAIcon';

const WarningIcon = ({asLead = false, text}) => (
  <FAIcon
    icon="exclamation-triangle"
    extraClassname={classNames('icon', 'icon--warning', 'icon--no-pointer', {
      'icon--as-lead': asLead,
    })}
    accessibleLabel={text}
  />
);

WarningIcon.propTypes = {
  asLead: PropTypes.bool,
  text: PropTypes.string,
};

export default WarningIcon;
