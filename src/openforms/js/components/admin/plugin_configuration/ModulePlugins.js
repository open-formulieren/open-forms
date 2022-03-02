import React from 'react';
import PropTypes from 'prop-types';
import {produce} from 'immer';

import PluginConfig from './PluginConfig';


const ModulePlugins = ({ module, plugins, currentConfiguration={}, onChange }) => {

    const onPluginToggle = (identifier, enabled) => {
        const newConfiguration = produce(currentConfiguration, draft => {
            if (!draft[identifier]) draft[identifier] = {};
            draft[identifier].enabled = enabled;
        });
        onChange(identifier, newConfiguration);
    };

    return (
        <div className="plugins-module">
            <div className="plugins-module__module">{module}</div>
            {
                plugins.map(({identifier, label}) => (
                    <PluginConfig
                        key={identifier}
                        module={module}
                        plugin={identifier}
                        label={label}
                        enabled={currentConfiguration[identifier]?.enabled ?? true}
                        onChange={(enabled) => onPluginToggle(identifier, enabled)}
                    />
                ))
            }
        </div>
    );
};

ModulePlugins.propTypes = {
    module: PropTypes.string.isRequired,
    plugins: PropTypes.arrayOf(PropTypes.shape({
        identifier: PropTypes.string,
        label: PropTypes.string,
    })),
    currentConfiguration: PropTypes.objectOf(PropTypes.shape({
        enabled: PropTypes.bool,
    })),
    onChange: PropTypes.func,
};


export default ModulePlugins;
