import classNames from 'classnames';
import {useContext, useId, useState} from 'react';

import {ValidationErrorContext} from './ValidationErrors';
import type {ValidationErrorTuple} from './ValidationErrors';

const checkHasErrors = (errors: ValidationErrorTuple[] = [], fieldNames: string[]): boolean => {
  // no field names known -> we don't know what to check, so assume no errors inside
  if (!fieldNames.length) return false;
  // check the error keys against the fieldName list
  for (const error of errors) {
    const errorKey = error[0];
    // check for exact membership
    if (fieldNames.includes(errorKey)) return true;
    // check for key prefix match for potential nested errors
    const partialMatch = fieldNames.some(name => errorKey.startsWith(`${name}.`));
    if (partialMatch) return true;
  }
  return false;
};

interface FieldsetProps {
  title?: React.ReactNode;
  extraClassName?: string;
  collapsible?: boolean;
  initialCollapsed?: boolean;
  children: React.ReactNode;
  /**
   * List of field names to monitor for validation errors.
   *
   * If validation errors are present for any of these fields, and the fieldset is in
   * collapsed state -> ensure that the fieldset is initially opened.
   */
  fieldNames?: string[];
}

const Fieldset: React.FC<FieldsetProps> = ({
  title = '',
  children,
  extraClassName,
  collapsible,
  initialCollapsed = true,
  fieldNames = [],
  ...extra
}) => {
  const [isOpen, setIsOpen] = useState(!initialCollapsed);
  const validationErrors = useContext(ValidationErrorContext);
  const hasErrorsInside = checkHasErrors(validationErrors, fieldNames);
  const titleId = useId();

  if (!isOpen && hasErrorsInside) {
    setIsOpen(true);
  }

  const titleNode = title ? (
    <h2 className="fieldset-heading" id={titleId}>
      {title}
    </h2>
  ) : null;
  const className = classNames('module', 'aligned', extraClassName, {
    'collapse in show': collapsible,
  });

  return (
    <fieldset className={className} aria-labelledby={title ? titleId : undefined} {...extra}>
      {titleNode && collapsible ? (
        <details open={isOpen}>
          <summary
            onClick={e => {
              e.preventDefault();
              setIsOpen(!isOpen);
            }}
          >
            {titleNode}
          </summary>
          {children}
        </details>
      ) : (
        <>
          {titleNode}
          {children}
        </>
      )}
    </fieldset>
  );
};

export default Fieldset;
