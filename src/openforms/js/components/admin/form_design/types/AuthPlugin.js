import PropTypes from 'prop-types';


const AuthPlugin = PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.oneOfType([PropTypes.string, PropTypes.node]).isRequired,
    providesAuth: PropTypes.arrayOf(PropTypes.string),
});


export default AuthPlugin;
