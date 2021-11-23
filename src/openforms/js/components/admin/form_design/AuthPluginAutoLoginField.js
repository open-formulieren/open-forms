import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import {Checkbox} from '../forms/Inputs';

const AuthPluginAutoLoginField = ({availableAuthPlugins, selectedAuthPlugins, selectedAuthPlugin, onChange, errors}) => {
    let filteredPlugins = availableAuthPlugins.filter(plugin => selectedAuthPlugins.includes(plugin.id))
    const authCheckboxes = filteredPlugins.map(plugin => {
        const providedAttributes = (
            <FormattedMessage
                description="Auth plugin provided attributes suffix"
                defaultMessage="(provides {attrs})"
                values={{attrs: plugin.providesAuth.join(', ')}}
            />
        );
        const label = (
            <>
                {plugin.label}
                {plugin.providesAuth.length ? (<>{' '}{providedAttributes}</>) : null}
            </>
        );

        return (
            <li key={plugin.id}>
                <Checkbox
                    name={`${plugin.label}_autologin`}
                    value={plugin.id}
                    label={label}
                    onChange={onChange}
                    checked={selectedAuthPlugin === plugin.id}
                />
            </li>
        );
    });

    return (
        <Field
            name="formAuthPluginAutoLogin"
            label={<FormattedMessage defaultMessage="Authentication automatic login" description="Auth plugin field label" />}
            helpText={<FormattedMessage defaultMessage="Select which authentication backend is automatically redirected to." description="Auth plugin field help text" />}
            errors={errors}
            required
        >
            <ul>{authCheckboxes}</ul>
        </Field>
    );
};

AuthPluginAutoLoginField.propTypes = {
    availableAuthPlugins: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        label: PropTypes.string,
        providesAuth: PropTypes.arrayOf(PropTypes.string)
    })),
    selectedAuthPlugin: PropTypes.string,
    onChange: PropTypes.func,
    required: PropTypes.bool,
    errors: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
};

export default AuthPluginAutoLoginField;
