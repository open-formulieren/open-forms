import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import {Radio} from '../forms/Inputs';

const AuthPluginAutoLoginField = ({name, availablePlugins, selectedPlugins, selectedPlugin, onChange}) => {
    let filteredPlugins = availablePlugins.filter(plugin => selectedPlugins.includes(plugin.id))
    filteredPlugins.unshift({
        id: "",
        label: <FormattedMessage defaultMessage="(none)" description="Label for option to disable autoLoginAuthenticationBackend" />}
    )  // Add empty option

    const AuthPluginAutoLoginFieldOptions = ({name, ...radioProps}) => (
        <ul>
            {filteredPlugins.map(plugin => (
                <li key={plugin.id}>
                    <Radio
                        name={name}
                        idFor={`id_${name}.${plugin.id ? plugin.id : "empty"}`}  // ensure idFor is unique
                        value={plugin.id}
                        label={plugin.label}
                        checked={selectedPlugin === plugin.id}
                        {...radioProps}
                    />
                </li>
            ))}
        </ul>
    );
    return (
        <AuthPluginAutoLoginFieldOptions name={name} onChange={onChange}></AuthPluginAutoLoginFieldOptions>
    );
};

AuthPluginAutoLoginField.propTypes = {
    availablePlugins: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        label: PropTypes.string,
        providesAuth: PropTypes.arrayOf(PropTypes.string)
    })),
    selectedPlugin: PropTypes.string,
    onChange: PropTypes.func,
};

export default AuthPluginAutoLoginField;
