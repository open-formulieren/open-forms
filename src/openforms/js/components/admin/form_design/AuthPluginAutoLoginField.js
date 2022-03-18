import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import {Checkbox} from '../forms/Inputs';

const AuthPluginAutoLoginField = ({availablePlugins, selectedPlugins, selectedPlugin, onChange, errors}) => {
    let filteredPlugins = availablePlugins.filter(plugin => selectedPlugins.includes(plugin.id))
    const authCheckboxes = filteredPlugins.map(plugin => {
        return (
            <li key={plugin.id}>
                <Checkbox
                    name={`autoLoginAuthenticationBackend.${plugin.id}`}
                    value={plugin.id}
                    label={plugin.label}
                    onChange={onChange}
                    checked={selectedPlugin === plugin.id}
                />
            </li>
        );
    });

    return (
        <Field
            name="formAuthPluginAutoLogin"
            label={<FormattedMessage defaultMessage="Authentication automatic login" description="Auto-login field label" />}
            helpText={<FormattedMessage defaultMessage="Select which authentication backend is automatically redirected to." description="Auto-login field help text" />}
            errors={errors}
            required
        >
            <ul>{authCheckboxes}</ul>
        </Field>
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
    errors: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
};

export default AuthPluginAutoLoginField;
