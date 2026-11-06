import classNames from 'classnames';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';
import type {IntlShape} from 'react-intl';

import {PrefixContext} from './Context';
import ErrorList from './ErrorList';
import type {ValidationError} from './ValidationErrors';

type NamedErrorMessage = [string, string];
type ErrorMessage = ValidationError | NamedErrorMessage;

export const normalizeErrors = (
  errors: ErrorMessage | ErrorMessage[] = [],
  intl: IntlShape
): [boolean, string[]] => {
  if (!Array.isArray(errors)) {
    errors = [errors];
  }
  const hasErrors = Boolean(errors && errors.length);
  const formattedErrors = errors.map(error => {
    if (typeof error === 'string') return error;
    if (!Array.isArray(error)) return intl.formatMessage(error);

    const [, msg] = error;
    return msg;
  });
  return [hasErrors, formattedErrors];
};

interface FieldProps {
  name: string;
  label?: React.ReactNode;
  helpText?: string;
  required?: boolean;
  disabled?: boolean;
  errors?: ValidationError[];
  children: React.ReactNode;
  fieldBox?: boolean;
  errorClassPrefix?: string;
  errorClassModifier?: string;
  noManageChildProps?: boolean;
  extraModifiers?: string[];
}

/**
 * Wrap a single form field, providing the label with correct attributes
 */
const Field: React.FC<FieldProps> = ({
  name,
  label = '',
  helpText = '',
  required = false,
  disabled = false,
  errors = [],
  children,
  fieldBox = false,
  errorClassPrefix = '',
  errorClassModifier = '',
  noManageChildProps = false,
  extraModifiers = [],
}) => {
  const intl = useIntl();
  const originalName = name;
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;

  const htmlFor = `id_${name}`;

  const manageChildProps = !noManageChildProps;
  let modifiedChildren = children;
  if (manageChildProps) {
    const childProps: {id: string; name: string; disabled?: boolean} = {
      id: htmlFor,
      name: originalName,
    };
    if (disabled) {
      childProps.disabled = true;
    }
    modifiedChildren = React.isValidElement(children)
      ? React.cloneElement(children, childProps)
      : undefined;
  }
  const [hasErrors, formattedErrors] = normalizeErrors(errors, intl);

  const fieldClassName = classNames(
    'flex-container',
    {
      fieldBox: fieldBox,
      errors: hasErrors,
    },
    ...extraModifiers
  );
  const wrapperClassName = classNames({'field--disabled': disabled});

  const fieldInputMarkup = (
    <div className={fieldClassName}>
      {label && (
        <label className={required ? 'required' : ''} htmlFor={htmlFor}>
          {label}
        </label>
      )}
      {modifiedChildren}
    </div>
  );

  const errorsMarkup = hasErrors && (
    <ErrorList classNamePrefix={errorClassPrefix} classNameModifier={errorClassModifier}>
      {formattedErrors}
    </ErrorList>
  );

  const helpMarkup = helpText && (
    <div className="help" id={`id_${name}_helptext`}>
      <div>{helpText}</div>
    </div>
  );

  return fieldBox ? (
    <div className={wrapperClassName}>
      {errorsMarkup}
      {fieldInputMarkup}
      {helpMarkup}
    </div>
  ) : (
    <>
      {errorsMarkup}
      <div className={wrapperClassName}>
        {fieldInputMarkup}
        {helpMarkup}
      </div>
    </>
  );
};

export default Field;
