import PropTypes from 'prop-types';

const AuthPlugin = PropTypes.shape({
  id: PropTypes.string.isRequired,
  label: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
  providesAuth: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(PropTypes.string)])
    .isRequired,
  // Schema will be null for plugins that don't support additional configuration
  schema: PropTypes.object,
});

export default AuthPlugin;
