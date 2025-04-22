import PropTypes from 'prop-types';

import LoAOverride from 'components/admin/form_design/authentication/LoAOverride';

const DigidOptionsForm = ({name, plugin, authBackend, onChange}) => {
  return (
    <LoAOverride
      name={`${name}.options.loa`}
      plugin={plugin}
      loa={authBackend.options.loa}
      onChange={onChange}
    />
  );
};

DigidOptionsForm.propType = {
  name: PropTypes.string.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    // Options configuration shape is specific to plugin
    options: PropTypes.object,
  }).isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default DigidOptionsForm;
