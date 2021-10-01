import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import {PrefixContext} from './Context';
import ErrorList from './ErrorList';

/**
 * Wrap a single form field, providing the label with correct attributes
 */
const Field = ({ name, label, helpText='', required=false, errors=[], children, fieldBox=false }) => {
    const originalName = name;
    const prefix = useContext(PrefixContext);
    name = prefix ? `${prefix}-${name}` : name;

    const htmlFor = `id_${name}`;

    const modifiedChildren = React.cloneElement(
        children,
        {id: htmlFor, name: originalName},
    );

    if( typeof errors === 'string' ) {
        errors = [ errors ];
    }

    const hasErrors = Boolean(errors && errors.length);
    const className = classNames(
        {'fieldBox': fieldBox},
        {'errors': hasErrors},
    );

    return (
        <>
            { !fieldBox && hasErrors ? <ErrorList>{errors}</ErrorList> : null }
            <div className={className}>
                { fieldBox && hasErrors ? <ErrorList>{errors}</ErrorList> : null }
                <label className={ required ? 'required': '' } htmlFor={htmlFor}>{label}</label>
                {modifiedChildren}
                { helpText ? <div className="help">{helpText}</div> : null }
            </div>
        </>
    );
};

Field.propTypes = {
    name: PropTypes.string.isRequired,
    label: PropTypes.node.isRequired,
    children: PropTypes.element.isRequired,
    helpText: PropTypes.node,
    required: PropTypes.bool,
    errors: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
    fieldBox: PropTypes.bool,
};


export default Field;
