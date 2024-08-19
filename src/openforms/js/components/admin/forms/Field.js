import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';

import {PrefixContext} from './Context';
import ErrorList from './ErrorList';

export const normalizeErrors = (errors = [], intl) => {
  if (!Array.isArray(errors)) {
    errors = [errors];
  }
  const hasErrors = Boolean(errors && errors.length);
  const formattedErrors = errors.map(error => {
    if (typeof error === 'string') return error;

    if (error.defaultMessage) return intl.formatMessage(error);

    const [, msg] = error;
    return msg;
  });
  return [hasErrors, formattedErrors];
};

/**
 * Wrap a single form field, providing the label with correct attributes
 */
const Field = ({
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
}) => {
  const intl = useIntl();
  const originalName = name;
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;

  const htmlFor = `id_${name}`;

  const manageChildProps = !noManageChildProps;
  let modifiedChildren = children;
  if (manageChildProps) {
    const childProps = {id: htmlFor, name: originalName};
    if (disabled) {
      childProps.disabled = true;
    }
    modifiedChildren = React.cloneElement(children, childProps);
  }
  const [hasErrors, formattedErrors] = normalizeErrors(errors, intl);
  const className = classNames({
    fieldBox: fieldBox,
    errors: hasErrors,
    'field--disabled': disabled,
  });

  return (
    <>
      {!fieldBox && hasErrors ? (
        <ErrorList classNamePrefix={errorClassPrefix} classNameModifier={errorClassModifier}>
          {formattedErrors}
        </ErrorList>
      ) : null}
      <div className={className}>
        {fieldBox && hasErrors ? (
          <ErrorList classNamePrefix={errorClassPrefix} classNameModifier={errorClassModifier}>
            {formattedErrors}
          </ErrorList>
        ) : null}

        <div className="flex-container">
          {label && (
            <label className={required ? 'required' : ''} htmlFor={htmlFor}>
              {label}
            </label>
          )}
          {modifiedChildren}
        </div>

        {helpText ? (
          <div className="help" id={`id_${name}_helptext`}>
            <div>{helpText}</div>
          </div>
        ) : null}
      </div>
    </>
  );
};

Field.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node,
  children: PropTypes.element.isRequired,
  helpText: PropTypes.node,
  required: PropTypes.bool,
  errors: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.array])),
    PropTypes.string,
  ]),
  fieldBox: PropTypes.bool,
  disabled: PropTypes.bool,
};

export default Field;
