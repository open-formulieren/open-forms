import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import {ComponentsContext} from './forms/Context';


/**
 * Render a string representation of a component identified by its key.
 * @param  {String} options.key The (unique) key of the component. Note that this key
 *                              should be unique across the entire form and all steps.
 * @return {String              The textual representation - label including step
 *                              information if available, otherwise the component label
 *                              and as a last resort the key itself is rendered.
 */
const FormioComponentRepresentation = ({ componentKey }) => {
    const allComponents = useContext(ComponentsContext);
    const component = allComponents[componentKey];
    const {stepLabel, label} = component;
    return ( stepLabel || label || componentKey );
};

FormioComponentRepresentation.propTypes = {
    componentKey: PropTypes.string.isRequired,
};


export default FormioComponentRepresentation;
