import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import {Checkbox} from '../forms/Inputs';
import Loader from '../Loader';

const AuthPluginField = ({loading, availableAuthPlugins, selectedAuthPlugins, onChange, errors}) => {
    const authCheckboxes = Object.entries(availableAuthPlugins).map(([pluginId, plugin]) => {
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
            <li key={pluginId}>
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
            {loading ? <Loader/> : <ul>{authCheckboxes}</ul>}
        </Field>
    );
};

AuthPluginField.propTypes = {
    loading: PropTypes.bool.isRequired,
    availableAuthPlugins: PropTypes.objectOf(PropTypes.shape({
        id: PropTypes.string,
        label: PropTypes.string,
        providesAuth: PropTypes.arrayOf(PropTypes.string)
    })),
    selectedAuthPlugins: PropTypes.arrayOf(PropTypes.string).isRequired,
    onChange: PropTypes.func,
    required: PropTypes.bool,
    errors: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
    ]),
};

export default AuthPluginField;
