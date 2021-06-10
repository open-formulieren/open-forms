import React from 'react';
import PropTypes from 'prop-types';
import usePrevious from 'react-use/esm/usePrevious';

import FormIOBuilder from '../formio_builder/builder';

const emptyConfiguration = {
    display: 'form',
};


/**
 * Load the form builder for a given form definition.
 *
 * Note that we only pass the initial configuration - DO NOT pass parent state back as
 * configuration, since this causes problems (bug https://github.com/formio/react/issues/386).
 *
 * The builder maintains its own state, and we can solely use the onChange handler to
 * keep track of our own 'application' state to eventually persist the data. This goes
 * against React's best practices, but we're fighting the library at this point.
 *
 * TODO: check what happens when we *replace* the form definition
 *
 */
const FormStepDefinition = ({ initialConfiguration=emptyConfiguration, onChange }) => {
    const prevConfiguration = usePrevious(initialConfiguration);

    if (prevConfiguration != null) {
        // mimick the checks use by the react-formio FormBuilder component
        if (
            prevConfiguration.display !== initialConfiguration.display
            || (prevConfiguration.components !== initialConfiguration.components)
        ) {
            console.error(
                ```
                The initialConfiguration prop was changed, which causes a re-render of the
                FormIOBuilder component which has known bugs. Please see the docstring of
                the FormStepDefinition component for more information.
                ```
            );
        }
    }

    return (
        <div className="form-definition">
            {<FormIOBuilder configuration={initialConfiguration} onChange={onChange} />}
        </div>
    );
};

FormStepDefinition.propTypes = {
    initialConfiguration: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default FormStepDefinition;
