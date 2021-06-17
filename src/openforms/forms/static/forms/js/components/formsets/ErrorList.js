import React from 'react';
import PropTypes from 'prop-types';


const ErrorList = ({ children }) => {
    const errors = React.Children.map(children, (error, i) => {
        return (<li key={i}>{error}</li>);
    })
    if (!errors) return null;

    return (
        <div className="errors">
            <ul className="errorlist">
                {errors}
            </ul>
        </div>
    );
};

ErrorList.propTypes = {
    children: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
};


export default ErrorList;
