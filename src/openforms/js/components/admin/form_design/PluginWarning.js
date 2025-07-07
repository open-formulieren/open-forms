import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';

import {FormContext} from './Context';

const PluginWarning = ({loginRequired, configuration}) => {
  const formContext = useContext(FormContext);
  const {availableAuthPlugins, selectedAuthPlugins, availablePrefillPlugins} = formContext.plugins;

  let warnings = [];

  // Check if the components in this definition require a prefill.
  // If yes, check that the attribute needed by the prefill is provided by at least one auth plugin
  const checkPrefillsAuth = configuration => {
    if (!availableAuthPlugins.length) return;

    if (configuration.components) {
      configuration.components.map(checkPrefillsAuth);
    }

    const pluginId = configuration?.prefill?.plugin;
    if (!pluginId) return;

    const prefillPlugin = availablePrefillPlugins.find(plugin => plugin.id === pluginId);
    const requiredAuthAttribute = prefillPlugin.requiresAuth;

    if (!requiredAuthAttribute) return;

    // Iterate over the selected plugins and check if they provide the required Auth attribute
    let pluginProvidesAttribute = false;
    for (const pluginName of selectedAuthPlugins) {
      const authPlugin = availableAuthPlugins.find(plugin => plugin.id === pluginName);
      if (!authPlugin) break;

      if (requiredAuthAttribute.some(attr => authPlugin.providesAuth.includes(attr))) {
        pluginProvidesAttribute = true;
        break;
      }
    }

    if (!pluginProvidesAttribute) {
      const warning = (
        <FormattedMessage
          description="Prefill plugin requires unavailable auth attribute warning"
          defaultMessage={
            'Component "{label}" uses a prefill that requires one of the "{requiredAuthAttribute}" attributes. \
            Please select one or more authentication plugins that provide such an attribute.'
          }
          values={{
            label: configuration.label,
            requiredAuthAttribute: requiredAuthAttribute.join(', '),
          }}
        />
      );
      warnings.push(warning);
    }
  };

  const checkLoginRequired = loginRequired => {
    if (loginRequired && selectedAuthPlugins.length === 0) {
      warnings.push(
        <FormattedMessage
          description="No authentication backend selected warning."
          defaultMessage="This form step requires a login, but no authentication backend has been specified."
        />
      );
    }
  };

  checkLoginRequired(loginRequired);
  checkPrefillsAuth(configuration);

  if (warnings.length > 0) {
    const messages = warnings.map(warning => ({
      level: 'warning',
      message: warning,
    }));
    return <MessageList messages={messages} />;
  }

  return null;
};

PluginWarning.propTypes = {
  loginRequired: PropTypes.bool.isRequired,
  configuration: PropTypes.object.isRequired,
};

export default PluginWarning;
