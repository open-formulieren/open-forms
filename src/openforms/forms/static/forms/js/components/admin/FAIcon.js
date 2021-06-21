import React from 'react';
import PropTypes from 'prop-types';


const FAIcon = ({ icon, title, extraClassname='', ...props }) => {
    let className = `fa fa-${icon}`;
    if (extraClassname) {
        className += ` ${extraClassname}`;
    }
    return (
        <i className={className} title={title} {...props}></i>
    );
};

FAIcon.propTypes = {
    icon: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    extraClassname: PropTypes.string,
};


export default FAIcon;
