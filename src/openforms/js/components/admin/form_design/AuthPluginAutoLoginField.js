import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import {Radio} from '../forms/Inputs';
import RadioList from '../forms/RadioList';
import TYPES from './types';


const AuthPluginRadio = ({ name, index, plugin, checked=false, onChange }) => (
    <Radio
        name={name}
        idFor={`id_${name}_${index}`}  // ensure idFor is unique
        value={plugin.id}
        label={plugin.label}
        checked={checked}
        onChange={onChange}
    />
);

AuthPluginRadio.propTypes = {
    name: PropTypes.string.isRequired,
    index: PropTypes.number.isRequired,
    plugin: TYPES.AuthPlugin.isRequired,
    checked: PropTypes.bool,
};


const AuthPluginAutoLoginField = ({name, eligiblePlugins, value, onChange}) => {
    // Add empty/reset option
    const emptyOption = {
        id: '',
        label: <FormattedMessage defaultMessage="(none)" description="Label for option to disable autoLoginAuthenticationBackend" />,
    };
    return (
        <RadioList keyProp="plugin.id">
            {[emptyOption, ...eligiblePlugins].map((plugin, index) => (
                <AuthPluginRadio
                    key={plugin.id}
                    name={name}
                    index={index}
                    plugin={plugin}
                    checked={plugin.id === value}
                    onChange={onChange}
                />
            ))}
        </RadioList>
    );
};

AuthPluginAutoLoginField.propTypes = {
    name: PropTypes.string,  // usually injected by parent Field component
    eligiblePlugins: PropTypes.arrayOf(TYPES.AuthPlugin),
    value: PropTypes.string,
    onChange: PropTypes.func.isRequired,
};

export default AuthPluginAutoLoginField;
