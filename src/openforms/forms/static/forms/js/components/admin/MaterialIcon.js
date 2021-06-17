import React from 'react';
import PropTypes from 'prop-types';


const MaterialIcon = ({ icon, title, extraClassname='', ...props }) => {
    let className = `${icon} material-icons`;
    if (extraClassname) {
        className += ` ${extraClassname}`;
    }
    return (
        <i className={className} title={title} {...props}></i>
    );
};

MaterialIcon.propTypes = {
    icon: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    extraClassname: PropTypes.string,
};


export default MaterialIcon;
