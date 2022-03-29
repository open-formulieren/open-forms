import React from 'react';
import PropTypes from 'prop-types';


const ErrorList = ({ classNamePrefix, children }) => {
    const ulClassNames = 'errorlist ' + (classNamePrefix ? classNamePrefix + '__errors' : '');
    const errors = React.Children.map(children, (error, i) => (
        <li
            key={i}
            className={classNamePrefix ? `${classNamePrefix}__error` : ''}
        >{error}</li>
    ));
    if (!errors) return null;

    return (
        <ul className={ulClassNames}>
            {errors}
        </ul>
    );
};

ErrorList.propTypes = {
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
    classNamePrefix: PropTypes.string,
};


export default ErrorList;
