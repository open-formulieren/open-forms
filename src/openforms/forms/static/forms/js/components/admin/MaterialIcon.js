import React from 'react';
import PropTypes from 'prop-types';


const MaterialIcon = ({ icon, title, extraClassname='', component: Component='span', ...props }) => {
    let className = 'material-icons';
    if (extraClassname) {
        className += ` ${extraClassname}`;
    }
    return (
        <Component className={className} title={title} {...props}>
            {icon}
        </Component>
    );
};

MaterialIcon.propTypes = {
    icon: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    extraClassname: PropTypes.string,
};


export default MaterialIcon;
