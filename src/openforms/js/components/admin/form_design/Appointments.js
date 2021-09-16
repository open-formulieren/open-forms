import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import ComponentSelection from '../forms/ComponentSelection';
import {ComponentsContext} from '../forms/Context';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';



const initialState = {
    products: '',
    locations: '',
    dates: '',
    times: '',
    lastName: '',
    birthDate: '',
};


const reducer = (draft, action) => {
    switch(action.type) {
        case 'APPOINTMENTS_CONFIGURATION_CHANGED': {
            const {name, value} = action.payload;
            draft[name] = value;

            // If the component that is selected was already set for something else, clear the other
            //   thing it was set for since each component can only be used for one thing
            Object.entries(draft).map(([draftName, draftValue]) => {
                if (name !== draftName && value === draftValue) {
                    draft[draftName] = '';
                }
            });

            break;
        }
        default: {
            throw new Error(`Unknown action type: ${action.type}`);
        }
    }
};


const Appointments = ({ availableComponents={}, onChange }) => {

    let updateState = {};
    Object.entries(availableComponents).map(([key, component]) => {
        if (component['appointments.showProducts']) {
            updateState.products = key;
        } else if (component['appointments.showLocations']) {
            updateState.locations = key;
        } else if (component['appointments.showDates']) {
            updateState.dates = key;
        } else if (component['appointments.showTimes']) {
            updateState.times = key;
        } else if (component['appointments.lastName']) {
            updateState.lastName = key;
        } else if (component['appointments.birthDate']) {
            updateState.birthDate = key;
        }
    });

    const [state, dispatch] = useImmerReducer(reducer, {...initialState, ...updateState});

    const onFieldChange = (event) => {
        const {name, value} = event.target;
        dispatch({
            type: 'APPOINTMENTS_CONFIGURATION_CHANGED',
            payload: {
                name,
                value
            },
        });
        onChange(name, value);
    };

    const { products, locations, dates, times, lastName, birthDate } = state;

    return (
        <ComponentsContext.Provider value={availableComponents}>
            <Fieldset>
                <FormRow>
                    <Field
                        name="products"
                        label={<FormattedMessage defaultMessage="Products Component" description="Products Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where products for an appointment will be shown" description="Products Component field help text" />}
                    >
                        <ComponentSelection
                            name="productsComponentSelection"
                            value={products}
                            onChange={onFieldChange}
                            filter={(component) => (component.type === 'select')}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset>
                <FormRow>
                    <Field
                        name="locations"
                        label={<FormattedMessage defaultMessage="Locations Component" description="Locations Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where locations for an appointment will be shown" description="Locations Component field help text" />}
                    >
                        <ComponentSelection
                            name="locationsComponentSelection"
                            value={locations}
                            onChange={onFieldChange}
                            filter={(component) => (component.type === 'select')}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset>
                <FormRow>
                    <Field
                        name="dates"
                        label={<FormattedMessage defaultMessage="Dates Component" description="Dates Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where dates for an appointment will be shown" description="Dates Component field help text" />}
                    >
                        <ComponentSelection
                            name="datesComponentSelection"
                            value={dates}
                            onChange={onFieldChange}
                            filter={(component) => (component.type === 'select')}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset>
                <FormRow>
                    <Field
                        name="times"
                        label={<FormattedMessage defaultMessage="Times Component" description="Times Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where times for an appointment will be shown" description="Times Component field help text" />}
                    >
                        <ComponentSelection
                            name="timesComponentSelection"
                            value={times}
                            onChange={onFieldChange}
                            filter={(component) => (component.type === 'select')}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset>
                <FormRow>
                    <Field
                        name="lastName"
                        label={<FormattedMessage defaultMessage="Last Name Component" description="Last Name Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where last name for an appointment will be shown" description="Last Name Component field help text" />}
                    >
                        <ComponentSelection
                            name="lastNameComponentSelection"
                            value={lastName}
                            onChange={onFieldChange}
                            filter={(component) => (component.type === 'textfield')}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset>
                <FormRow>
                    <Field
                        name="birthDate"
                        label={<FormattedMessage defaultMessage="Birth Date Component" description="Birth Date Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where birth date for an appointment will be shown" description="Birth Date Component field help text" />}
                    >
                        <ComponentSelection
                            name="birthDateComponentSelection"
                            value={birthDate}
                            onChange={onFieldChange}
                            filter={(component) => (component.type === 'date')}
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
