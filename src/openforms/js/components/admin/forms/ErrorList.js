import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';

const ErrorList = ({classNamePrefix = '', classNameModifier = '', children}) => {
  const additionalClassName = `${classNamePrefix}__errors`;
  const additionalClassNameModified = `${additionalClassName}--${classNameModifier}`;
  let ulClassNames = classNames(
    'errorlist',
    {[additionalClassName]: classNamePrefix},
    {[additionalClassNameModified]: classNameModifier}
  );

  const errors = React.Children.map(children, (error, i) => (
    <li key={i} className={classNamePrefix ? `${classNamePrefix}__error` : ''}>
      {error}
    </li>
  ));

  if (!errors) return null;

  return <ul className={ulClassNames}>{errors}</ul>;
};

ErrorList.propTypes = {
  children: PropTypes.oneOfType([PropTypes.arrayOf(PropTypes.string), PropTypes.string]),
  classNamePrefix: PropTypes.string,
  classNameModifier: PropTypes.string,
};

export default ErrorList;
