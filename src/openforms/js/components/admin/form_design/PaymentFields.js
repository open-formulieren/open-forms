import React from 'react';
import PropTypes from 'prop-types';


const PaymentFields = ({
    backends=[],
    selectedBackend='',
    backendOptions={},
    onChange
}) => {
    return (
        null
    );
};

PaymentFields.propTypes = {
    backends: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
        schema: PropTypes.shape({
            type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
            properties: PropTypes.object,
            required: PropTypes.arrayOf(PropTypes.string),
        }),
    })),
    selectedBackend: PropTypes.string,
    backendOptions: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default PaymentFields;
