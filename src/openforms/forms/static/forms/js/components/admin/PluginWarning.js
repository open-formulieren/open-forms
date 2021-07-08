import React, {useContext} from "react";
import {PluginsContext} from "./Context";
import PropTypes from "prop-types";


const PluginWarning = ({loginRequired, configuration}) => {
    const {selectedAuthPlugins, availableAuthPlugins, availablePrefillPlugins} = useContext(PluginsContext);

    let warnings = [];

    // Check if the components in this definition require a prefill.
    // If yes, check that the attribute needed by the prefill is provided by at least one auth plugin
    const checkPrefillsAuth = (configuration) => {
        if (availableAuthPlugins.loading) return;

        if (configuration.components) {
            configuration.components.map(checkPrefillsAuth);
        }

        if (configuration.prefill) {
            if (configuration.prefill.plugin !== '') {
                const requiredAuthAttribute = availablePrefillPlugins.data[configuration.prefill.plugin].requiresAuth;

                if (!requiredAuthAttribute) return;

                // Iterate over the selected plugins and check if they provide the required Auth attribute
                let pluginProvidesAttribute = false;
                for (const pluginName of selectedAuthPlugins) {
                    const authPlugin = availableAuthPlugins.data[pluginName];
                    if ( authPlugin.providesAuth.includes(requiredAuthAttribute) ) {
                        pluginProvidesAttribute = true;
                        break;
                    }
                }

                if ( !pluginProvidesAttribute ) {
                    warnings.push(`Component "${configuration.label}" uses a prefill that requires the "${requiredAuthAttribute}"
                    attribute. Please select an authentication plugin that provides this attribute.`);
                }
            }
        }
    };

    const checkLoginRequired = (loginRequired) => {
        if (loginRequired && selectedAuthPlugins.length === 0) {
            warnings.push('This form step requires a login, but no authentication backend has been specified.');
        }
    };

    checkLoginRequired(loginRequired);
    checkPrefillsAuth(configuration);

    if ( warnings.length > 0 ) {
     const formattedWarnings = warnings.map((item, index) => {
         return (
             <li key={index} className="warning" >
                 {item}
            </li>
         )
     })

     return (
        <ul className="messagelist">
            {formattedWarnings}
        </ul>
     );
    }

    return null;
};

PluginWarning.propTypes = {
    loginRequired: PropTypes.bool.isRequired,
    configuration: PropTypes.object.isRequired,
};

export default PluginWarning;
