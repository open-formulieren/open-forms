import React from 'react';
import PropTypes from 'prop-types';


const ValidationErrorContext = React.createContext([]);
ValidationErrorContext.displayName = 'ValidationErrorContext';


const ValidationErrorsProvider = ({ children, errors=[] }) => {
    return (
        <ValidationErrorContext.Provider value={errors}>
            {children}
        </ValidationErrorContext.Provider>
    );
};

ValidationErrorsProvider.propTypes = {
    errors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
};


export {ValidationErrorsProvider, ValidationErrorContext};
export default ValidationErrorsProvider;
