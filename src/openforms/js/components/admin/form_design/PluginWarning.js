import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import {PluginsContext} from './Context';
import MessageList from './warnings/MessageList';


const PluginWarning = ({loginRequired, configuration}) => {
    const {availableAuthPlugins, selectedAuthPlugins, availablePrefillPlugins} = useContext(PluginsContext);

    let warnings = [];

    // Check if the components in this definition require a prefill.
    // If yes, check that the attribute needed by the prefill is provided by at least one auth plugin
    const checkPrefillsAuth = (configuration) => {
        if (!availableAuthPlugins.length) return;

        if (configuration.components) {
            configuration.components.map(checkPrefillsAuth);
        }

        if (!(configuration.prefill && Object.keys(configuration.prefill).length && configuration.prefill.plugin !== '' )) return;

        const prefillPlugin = availablePrefillPlugins.find(plugin => plugin.id === configuration.prefill.plugin);
        const requiredAuthAttribute = prefillPlugin.requiresAuth;

        if (!requiredAuthAttribute) return;

        // Iterate over the selected plugins and check if they provide the required Auth attribute
        let pluginProvidesAttribute = false;
        for (const pluginName of selectedAuthPlugins) {

            const authPlugin = availableAuthPlugins.find(plugin => plugin.id === pluginName);
            if (!authPlugin) break;

            if ( authPlugin.providesAuth.includes(requiredAuthAttribute) ) {
                pluginProvidesAttribute = true;
                break;
            }
        }

        if ( !pluginProvidesAttribute ) {
            const warning = (
                <FormattedMessage
                    description="Prefill plugin requires unavailable auth attribute warning"
                    defaultMessage={
                        "Component \"{label}\" uses a prefill that requires the \"{requiredAuthAttribute}\" attribute. \
                        Please select an authentication plugin that provides this attribute."
                    }
                    values={{
                        label: configuration.label,
                        requiredAuthAttribute
                    }}
                />
            );
            warnings.push(warning);
        }
    };

    const checkLoginRequired = (loginRequired) => {
        if (loginRequired && selectedAuthPlugins.length === 0) {
            warnings.push(
                <FormattedMessage
                    description="No authentication backend selected warning."
                    defaultMessage="This form step requires a login, but no authentication backend has been specified." />
            );
        }
    };

    checkLoginRequired(loginRequired);
    checkPrefillsAuth(configuration);

    if ( warnings.length > 0 ) {
        return (<MessageList warnings={warnings} />);
    }

    return null;
};

PluginWarning.propTypes = {
    loginRequired: PropTypes.bool.isRequired,
    configuration: PropTypes.object.isRequired,
};

export default PluginWarning;
