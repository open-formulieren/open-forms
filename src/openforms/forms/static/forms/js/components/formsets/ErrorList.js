import React from 'react';
import PropTypes from 'prop-types';


const ErrorList = ({ children=[] }) => {
    if (!children.length) return null;
    return (
        <ul className="errorlist">
            {children.map((error, i) => (
                <li key={i}>{error}</li>
            ))}
        </ul>
    );
};

ErrorList.propTypes = {
    children: PropTypes.arrayOf(PropTypes.string),
};


export default ErrorList;
