import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import {PrefixContext} from './Context';
import {ValidationErrorContext} from './ValidationErrors';
import Field from './Field';


const FormRow = ({ fields=[], children }) => {
    const fieldClasses = fields.map(field => `field-${field}`);

    let hasErrors = false;
    const prefix = useContext(PrefixContext);
    const validationErrors = useContext(ValidationErrorContext);

    // process (validation) errors here
    const processedChildren = React.Children.map(children, child => {
        // check if it *looks* like a field
        const {name} = child.props;
        if (!name) return child;

        const childErrors = validationErrors.filter( ([key]) => key === name);
        if (childErrors.length > 0) {
            hasErrors = true;
        }
        return React.cloneElement(
            child,
            {errors: childErrors.map(([key, msg]) => msg)}
        );
    });

    const className = classNames(
        'form-row',
        {'errors': hasErrors},
        ...fieldClasses,
    );
    return (
        <div className={className}>
            {processedChildren}
        </div>
    );
};

FormRow.propTypes = {
    fields: PropTypes.arrayOf(PropTypes.string),
    children: PropTypes.node,
};

export default FormRow;
