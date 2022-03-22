import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import {Checkbox} from '../forms/Inputs';
import TYPES from './types';


const AuthPluginField = ({availableAuthPlugins, selectedAuthPlugins, onChange, errors}) => {
    const authCheckboxes = availableAuthPlugins.map(plugin => {
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
                    name={plugin.label}
                    value={plugin.id}
                    label={label}
                    onChange={onChange}
                    checked={selectedAuthPlugins.includes(plugin.id)}
                />
            </li>
        );
    });

    return (
        <Field
            name="formAuthPlugin"
            label={<FormattedMessage defaultMessage="Authentication" description="Auth plugin field label" />}
            helpText={<FormattedMessage defaultMessage="Select the allowed authentication plugins to log in at the start of the form." description="Auth plugin field help text" />}
            errors={errors}
            required
        >
            <ul>{authCheckboxes}</ul>
        </Field>
    );
};

AuthPluginField.propTypes = {
    availableAuthPlugins: PropTypes.arrayOf(TYPES.AuthPlugin).isRequired,
    selectedAuthPlugins: PropTypes.arrayOf(PropTypes.string).isRequired,
    onChange: PropTypes.func,
    required: PropTypes.bool,
    errors: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
};

export default AuthPluginField;
