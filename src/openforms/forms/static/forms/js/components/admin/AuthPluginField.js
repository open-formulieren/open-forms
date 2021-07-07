import Field from "../formsets/Field";
import {Checkbox} from "../formsets/Inputs";
import React from "react";
import Loader from "./Loader";
import PropTypes from "prop-types";

const AuthPluginField = ({loading, availableAuthPlugins, selectedAuthPlugins, onChange, errors}) => {
    const authCheckboxes = Object.keys(availableAuthPlugins).map((pluginId, index) => {
        const plugin = availableAuthPlugins[pluginId];
        const providedAttributes = `(provides ${plugin.providesAuth.join(', ')})`;
        const label = `${plugin.label} ${plugin.providesAuth.length > 0 ? providedAttributes : ''}`;

        return (
            <li key={index}>
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
            name='formAuthPlugin'
            label='Authentication'
            helpText='The authentication backends required to be able to fill in the form.'
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

export {AuthPluginField};
