import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';

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
    <Fieldset
      title={
        <FormattedMessage
          defaultMessage="{plugin} plugin options"
          description="Authentication plugin options configuration"
          values={{
            plugin: plugin.label,
          }}
        />
      }
    >
      <OptionsFormComponent
        name={name}
        plugin={plugin}
        authBackend={authBackend}
        onChange={onChange}
      />
    </Fieldset>
  );
};

AuthPluginOptions.propTypes = {
  index: PropTypes.number.isRequired,
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
      providesAuth: PropTypes.string,
    })
  ),
  onChange: PropTypes.func.isRequired,
};

export default AuthPluginOptions;
