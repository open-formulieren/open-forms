import React from 'react';
import PropTypes from 'prop-types';

import FormIOBuilder from '../formio_builder/builder';

const emptyConfiguration = {
    display: 'form',
};


/**
 * Load the form builder for a given form definition.
 *
 * Note that the underlying FormIOBuilder creates a ref from the configuration. The
 * actual builder state is maintained by FormioJS itself and we are not driven that
 * state via props - only the initial state!
 *
 * We can solely use the onChange handler to * keep track of our own 'application'
 * state to eventually persist the data. This goes * against React's best practices,
 * but we're fighting the library at this point.
 *
 * TODO: check what happens when we *replace* the form definition
 *
 */
const FormStepDefinition = ({ configuration=emptyConfiguration, onChange, ...props }) => {
    return (
        <div className="form-definition">
            {<FormIOBuilder configuration={configuration} onChange={onChange} {...props} />}
        </div>
    );
};

FormStepDefinition.propTypes = {
    configuration: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default FormStepDefinition;
