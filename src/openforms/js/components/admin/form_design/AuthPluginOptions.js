import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';

import {BACKEND_OPTIONS_FORMS} from './authentication/index';

const AuthPluginOptions = ({name, authBackend, availableAuthPlugins, onChange}) => {
  const plugin = availableAuthPlugins.find(authPlugin => authPlugin.id === authBackend.backend);
  if (!plugin?.schema) {
    return null;
  }

  const OptionsFormComponent = BACKEND_OPTIONS_FORMS[authBackend.backend]?.form;
  if (!OptionsFormComponent) {
    console.debug(
      `No configuration form known in the registry for plugin with ID '${authBackend.backend}'.`
    );
    return null;
  }

  return (
    <FormRow>
      <OptionsFormComponent
        name={name}
        label={
          <FormattedMessage
            defaultMessage="{plugin} plugin options"
            description="Authentication plugin options configuration"
            values={{
              plugin: plugin.label,
            }}
          />
        }
        plugin={plugin}
        authBackend={authBackend}
        onChange={({formData}) => onChange({target: {name, value: formData}})}
      />
    </FormRow>
  );
};

AuthPluginOptions.propTypes = {
  name: PropTypes.string.isRequired,
  authBackend: PropTypes.shape({
    backend: PropTypes.string.isRequired, // Auth plugin id
    // Options configuration shape is specific to plugin
    options: PropTypes.object,
  }).isRequired,
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(PropTypes.string)]),
    })
  ),
  onChange: PropTypes.func.isRequired,
};

export default AuthPluginOptions;
