import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';

import {PrefixContext} from './Context';
import ErrorList from './ErrorList';
import {useIntl} from 'react-intl';

export const normalizeErrors = (errors = [], intl) => {
  if (!Array.isArray(errors)) {
    errors = [errors];
  }
  const hasErrors = Boolean(errors && errors.length);
  const formattedErrors = errors.map(error => {
    if (typeof error === 'string') return error;

    if (error.defaultMessage) return intl.formatMessage(error);

    const [key, msg] = error;
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
  errors = [],
  children,
  fieldBox = false,
}) => {
  const intl = useIntl();
  const originalName = name;
  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;

  const htmlFor = `id_${name}`;

  const modifiedChildren = React.cloneElement(children, {id: htmlFor, name: originalName});
  const [hasErrors, formattedErrors] = normalizeErrors(errors, intl);
  const className = classNames({fieldBox: fieldBox}, {errors: hasErrors});

  return (
    <>
      {!fieldBox && hasErrors ? <ErrorList>{formattedErrors}</ErrorList> : null}
      <div className={className}>
        {fieldBox && hasErrors ? <ErrorList>{formattedErrors}</ErrorList> : null}
        {label && (
          <label className={required ? 'required' : ''} htmlFor={htmlFor}>
            {label}
          </label>
        )}
        {modifiedChildren}
        {helpText ? <div className="help">{helpText}</div> : null}
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
};

export default Field;
