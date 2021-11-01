import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import {ValidationErrorContext} from './ValidationErrors';


const FormRow = ({ fields=[], children }) => {
    const fieldClasses = fields.map(field => `field-${field}`);

    let hasErrors = false;
    const validationErrors = useContext(ValidationErrorContext);

    // process (validation) errors here
    const processedChildren = React.Children.map(children, child => {
        // check if it *looks* like a field
        const {name} = child.props;
        if (!name) return child;

        const childErrors = validationErrors
            .map( ([key, err]) => {
                // exact match on field & error key
                if (key === name) return [key, err];

                // check for nested errors
                const prefix = `${name}.`;
                if (key.startsWith(prefix)) {
                    const nestedKey = key.replace(prefix, '', 1);
                    return [nestedKey, err];
                }
                // not a relevant child error, return null which is filtered out later
                return null;
            })
            // filter out falsy values
            .filter(err => err);

        if (childErrors.length > 0) {
            hasErrors = true;
        }
        return React.cloneElement(
            child,
            {errors: childErrors}
        );
    });

    const className = classNames(
        'form-row',
        {'errors': processedChildren.length === 1 && hasErrors},
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
