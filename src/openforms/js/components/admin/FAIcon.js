import PropTypes from 'prop-types';
import React from 'react';

const FAIcon = ({icon, title, extraClassname = '', ...props}) => {
  let className = `fa-solid fa-${icon}`;
  if (extraClassname) {
    className += ` ${extraClassname}`;
  }
  return <i className={className} title={title} aria-label={title} {...props}></i>;
};

FAIcon.propTypes = {
  icon: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  extraClassname: PropTypes.string,
};

export default FAIcon;
