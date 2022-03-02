import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {produce} from 'immer';

import ModulePlugins from './ModulePlugins';


const PluginConfiguration = ({ name, modulesAndPlugins, value, onChange }) => {
    // we must track the config state in the component, since the DOM modifications
    // do not result in prop changes (this is the root component which is only mounted
    // once)
    const [currentConfig, setCurrentConfig] = useState(value);

    const onPluginChange = (module, identifier, newConfig) => {
        const newValue = produce(currentConfig, draft => {
            if (!draft[module]) draft[module] = {};
            draft[module][identifier] = newConfig[identifier];
        });
        onChange(newValue);
        setCurrentConfig(newValue);
    };

    return (
        <>
            {
                Object.entries(modulesAndPlugins).map(([module, plugins]) => (
                    <ModulePlugins
                        key={module}
                        module={module}
                        plugins={plugins}
                        currentConfiguration={currentConfig[module]}
                        onChange={ (identifier, newConfig) => onPluginChange(module, identifier, newConfig) }
                    />
                ))
            }
        </>
    );
};

PluginConfiguration.propTypes = {
    name: PropTypes.string.isRequired,
    modulesAndPlugins: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.shape({
        identifier: PropTypes.string,
        label: PropTypes.string,
    }))).isRequired,
    value: PropTypes.object.isRequired,
    onChange: PropTypes.func.isRequired,
};


export default PluginConfiguration;
