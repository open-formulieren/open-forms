import PropTypes from 'prop-types';

export const ErrorsType = PropTypes.oneOfType([
  PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.array])),
  PropTypes.string,
]);
