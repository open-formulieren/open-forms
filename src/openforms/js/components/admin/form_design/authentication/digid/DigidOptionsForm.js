import PropTypes from 'prop-types';

import LoAOverride from 'components/admin/form_design/authentication/LoAOverride';

const DigidOptionsForm = ({name, plugin, authBackend, onChange}) => (
  <LoAOverride
    name={`${name}.options.loa`}
    plugin={plugin}
    loa={authBackend.options.loa}
    onChange={onChange}
  />
);

DigidOptionsForm.propType = {
  name: PropTypes.string.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    options: PropTypes.shape({
      loa: PropTypes.string,
    }),
  }).isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    providesAuth: PropTypes.oneOf(['bsn']).isRequired,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        loa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
      }),
    }).isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default DigidOptionsForm;
