import PropTypes from 'prop-types';

const BackendType = PropTypes.shape({
  id: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }),
});

export {BackendType};
