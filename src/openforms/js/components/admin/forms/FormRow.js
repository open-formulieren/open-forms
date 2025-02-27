import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';

import {ValidationErrorContext} from './ValidationErrors';

const FormRow = ({fields = [], children, preventErrorsModifier = false}) => {
  const fieldClasses = fields.map(field => `field-${field}`);

  let hasErrors = false;
  const validationErrors = useContext(ValidationErrorContext);

  let hasAnyFieldBox = false;
  // process (validation) errors here
  const processedChildren = React.Children.map(children, child => {
    // check if it *looks* like a field
    let {name, errors, fieldBox = false} = child.props;
    if (fieldBox) hasAnyFieldBox = true;

    if (!name) return child;

    const childErrors = validationErrors
      .map(([key, err]) => {
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

    // Avoid overwriting errors if they are added directly on the child
    if ((errors && errors.length > 0) || childErrors.length > 0) {
      hasErrors = true;
    }
    return React.cloneElement(child, {errors: errors || childErrors});
  });

  const className = classNames(
    'form-row',
    {errors: processedChildren.length === 1 && hasErrors && !preventErrorsModifier},
    ...fieldClasses
  );
  const inner = hasAnyFieldBox ? (
    <div className="flex-container form-multiline">{processedChildren}</div>
  ) : (
    processedChildren
  );
  return <div className={className}>{inner}</div>;
};

FormRow.propTypes = {
  fields: PropTypes.arrayOf(PropTypes.string),
  children: PropTypes.node,

  /**
   * Prevents the 'errors' modifier from being added to the 'form-row' component.
   */
  preventErrorsModifier: PropTypes.bool,
};

export default FormRow;
