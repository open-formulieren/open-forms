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

        const childErrors = validationErrors.filter( ([key]) => {
            if (key === name) return true;
            const splitName = name.split('.');
            const splitKey = key.split('.');
            if (splitName.length <= splitKey.length) {
                for (let index = 0; index < splitName.length; index++) {
                    if (splitName[index] !== splitKey[index]) return false;
                }
                return true;
            }
            return false;
        });

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
