import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useId} from 'react';

import FAIcon from './FAIcon';

const WarningIcon = ({asLead = false, text = ''}) => {
  const id = useId();
  return (
    <>
      {text && (
        <span className="hidden" id={id}>
          {text}
        </span>
      )}
      <FAIcon
        icon="exclamation-triangle"
        extraClassname={classNames('icon', 'icon--warning', 'icon--no-pointer', {
          'icon--as-lead': asLead,
        })}
        title={text}
        aria-labelledby={text ? id : undefined}
      />
    </>
  );
};

WarningIcon.propTypes = {
  asLead: PropTypes.bool,
  text: PropTypes.string,
};

export default WarningIcon;
