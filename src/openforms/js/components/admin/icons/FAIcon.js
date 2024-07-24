import PropTypes from 'prop-types';
import React, {useId} from 'react';

const FAIcon = ({icon, title, accessibleLabel, extraClassname = '', ...props}) => {
  const id = useId();

  let className = `fa-solid fa-${icon}`;
  if (extraClassname) {
    className += ` ${extraClassname}`;
  }

  return (
    <>
      {accessibleLabel && (
        <span className="hidden" id={id}>
          {accessibleLabel}
        </span>
      )}
      <i
        className={className}
        title={title || accessibleLabel}
        aria-labelledby={accessibleLabel ? id : undefined}
        {...props}
      />
    </>
  );
};

FAIcon.propTypes = {
  icon: PropTypes.string.isRequired,
  accessibleLabel: PropTypes.string,
  title: PropTypes.string,
  extraClassname: PropTypes.string,
};

export default FAIcon;
