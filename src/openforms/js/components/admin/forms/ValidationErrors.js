import PropTypes from 'prop-types';
import React from 'react';

const ValidationErrorContext = React.createContext([]);
ValidationErrorContext.displayName = 'ValidationErrorContext';

const ValidationErrorsProvider = ({children, errors = []}) => {
  return (
    <ValidationErrorContext.Provider value={errors}>{children}</ValidationErrorContext.Provider>
  );
};

const errorArray = props => {
  const errorMsg = 'Invalid error passed to ValidationErrorsProvider.';

  if (props.length !== 2) return new Error(`${errorMsg} It should have length 2`);

  if (typeof props[0] !== 'string')
    return new Error(`${errorMsg} The error key should be a string.`);
  if (!(typeof props[1] === 'string' || props[1].defaultMessage))
    return new Error(`${errorMsg} The error msg should be a string or and intl object.`);
};

ValidationErrorsProvider.propTypes = {
  children: PropTypes.node,
  errors: PropTypes.arrayOf(PropTypes.arrayOf(errorArray)),
};

/**
 * Only return the errors that have the $name prefix.
 * @param  {string} name   Field name prefix
 * @param  {Array<[string, T>} errors List of all validation errors.
 * @return {Array<[string, T>} List of errors that match the name prefix.
 */
const filterErrors = (name, errors) => {
  return errors
    .filter(([key]) => key.startsWith(`${name}.`))
    .map(([key, msg]) => [key.slice(name.length + 1), msg]);
};

export {ValidationErrorsProvider, ValidationErrorContext, filterErrors};
export default ValidationErrorsProvider;
