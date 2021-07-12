import React from 'react';
import PropTypes from 'prop-types';


const FormRow = ({ fields=[], children }) => {
    const fieldClasses = fields.map(field => `field-${field}`).join(' ');
    return (
        <div className={`form-row ${fieldClasses}`}>
            {children}
        </div>
    );
};

FormRow.propTypes = {
    fields: PropTypes.arrayOf(PropTypes.string),
    children: PropTypes.node,
};

export default FormRow;
