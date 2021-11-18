import get from 'lodash/get';
import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import ComponentSelection from '../forms/ComponentSelection';
import {ComponentsContext} from '../forms/Context';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';

const PREFIX = 'appointments'; // prefix to use in the Formio.js component JSON

const KEYS = [
    'showProducts',
    'showLocations',
    'showDates',
    'showTimes',
    'lastName',
    'birthDate',
    'phoneNumber',
];


const AppointmentConfigurationComponentSelection = ({ currentConfiguration, configKey, filterType, onChange }) => (
    <ComponentSelection
        name={configKey}
        value={get(currentConfiguration, configKey, '')}
        onChange={onChange}
        filter={(component) => (component.type === filterType)}
    />
);

AppointmentConfigurationComponentSelection.propTypes = {
    currentConfiguration: PropTypes.objectOf(PropTypes.string).isRequired,
    configKey: PropTypes.oneOf(KEYS).isRequired,
    filterType: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};


const Appointments = ({ availableComponents={}, onChange }) => {
    // extract the current values from the component definitions
    const configuration = {}; // key: appointment configuration key, value: component key
    Object.entries(availableComponents).forEach(([componentKey, component]) =>{
        // check the component for any key present
        for (const configKey of KEYS) {
            const fullPath = `${PREFIX}.${configKey}`;
            const value = get(component, fullPath, null);
            if (!value) continue;

            configuration[configKey] = componentKey;
            // if a config key is found, break out so we exit at the first hit. There
            // should only ever be one hit, but in case something was corrupted, don't
            // let it break our own state.
            break;
        }
    });

    /**
     * On form field change handler.
     *
     * We simply invoke the parent handler, but ensure we use the prefixed name so that
     * the appropriate custom Formio.js component properties can be set
     * @param  {Event} event The React event for the changed DOM element.
     * @return {void}
     */
    const onFieldChange = (event) => {
        const {name, value} = event.target;
        const prefixedName = `${PREFIX}.${name}`;
        const fakeEvent = {
            target: {
                name: prefixedName,
                value: value,
            },
        };
        onChange(fakeEvent);
    };

    return (
        <ComponentsContext.Provider value={availableComponents}>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="products"
                        label={<FormattedMessage defaultMessage="Products Component" description="Products Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where products for an appointment will be shown" description="Products Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="showProducts"
                            onChange={onFieldChange}
                            filterType="select"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="locations"
                        label={<FormattedMessage defaultMessage="Locations Component" description="Locations Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where locations for an appointment will be shown" description="Locations Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="showLocations"
                            onChange={onFieldChange}
                            filterType="select"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="dates"
                        label={<FormattedMessage defaultMessage="Dates Component" description="Dates Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where dates for an appointment will be shown" description="Dates Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="showDates"
                            onChange={onFieldChange}
                            filterType="select"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="times"
                        label={<FormattedMessage defaultMessage="Times Component" description="Times Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where times for an appointment will be shown" description="Times Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="showTimes"
                            onChange={onFieldChange}
                            filterType="select"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="lastName"
                        label={<FormattedMessage defaultMessage="Last Name Component" description="Last Name Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where the last name should be entered" description="Last Name Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="lastName"
                            onChange={onFieldChange}
                            filterType="textfield"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="birthDate"
                        label={<FormattedMessage defaultMessage="Birth Date Component" description="Birth Date Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where the birth date should be entered" description="Birth Date Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="birthDate"
                            onChange={onFieldChange}
                            filterType="date"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset extraClassName="admin-fieldset">
                <FormRow>
                    <Field
                        name="phoneNumber"
                        label={<FormattedMessage defaultMessage="Phone Number Component" description="Phone Number Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where the phone number should be entered" description="Phone Number Component field help text" />}
                    >
                        <AppointmentConfigurationComponentSelection
                            currentConfiguration={configuration}
                            configKey="phoneNumber"
                            onChange={onFieldChange}
                            filterType="phoneNumber"
                        />
                    </Field>
                </FormRow>
            </Fieldset>
        </ComponentsContext.Provider>
    )
};

Appointments.propTypes = {
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
    onChange: PropTypes.func.isRequired,
};


export default Appointments;
export {KEYS};
