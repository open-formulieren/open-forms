import React from 'react';
import PropTypes from 'prop-types';


const User = ({ fullName, username, firstName, lastName, fullFirstName=false }) => {
    if (fullFirstName && fullName) return fullName;
    if (!fullFirstName && fullName) {
        const firstLetter = firstName ? firstName[0] : '';
        return `${firstLetter ? `${firstLetter}. ` : ''}${lastName}`;
    }
    // fallback
    return username;
};

User.propTypes = {
    fullName: PropTypes.string.isRequired,
    username: PropTypes.string.isRequired,
    firstName: PropTypes.string,
    lastName: PropTypes.string,
    fullFirstName: PropTypes.bool,
};


export default User;
