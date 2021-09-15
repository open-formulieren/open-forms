import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import ComponentSelection from './logic/ComponentSelection';
import {ComponentsContext} from './logic/Context';

import {FormLogic} from './FormLogic';

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

            // TODO
            // clear the dependent fields if needed - e.g. if the component changes, all fields to the right change
            // const currentFieldIndex = TRIGGER_FIELD_ORDER.indexOf(name);
            // const nextFieldNames = TRIGGER_FIELD_ORDER.slice(currentFieldIndex + 1);
            // for (const name of nextFieldNames) {
            //     draft[name] = initialState[name];
            // }
            break;
        }
        default: {
            throw new Error(`Unknown action type: ${action.type}`);
        }
    }
};


const Appointments = ({ availableComponents={}, onChange }) => {

    let updatedState = {};
    Object.entries(availableComponents).map(([key, comp]) => {
        if (comp.appointmentsShowProducts || comp.appointmentsShowLocations || comp.appointmentsShowDates ||
            comp.appointmentsShowTimes || comp.appointmentsLastName || comp.appointmentsBirthDate) {
            updatedState.products = key;
        }
    });

    const [state, dispatch] = useImmerReducer(reducer, {...initialState, ...updatedState});

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

    const {
        products,
        locations,
        dates,
        times,
        lastName,
        birthDate,
    } = state;


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
                            name="component"
                            value={products}
                            onChange={onFieldChange}
                            filter={(comp) => (comp.type === 'select')}
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
                            name="component"
                            value={locations}
                            onChange={onFieldChange}
                            filter={(comp) => (comp.type === 'select')}
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
                            name="component"
                            value={dates}
                            onChange={onFieldChange}
                            filter={(comp) => (comp.type === 'select')}
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
                            name="component"
                            value={times}
                            onChange={onFieldChange}
                            filter={(comp) => (comp.type === 'select')}
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
                            name="component"
                            value={lastName}
                            onChange={onFieldChange}
                            filter={(comp) => (comp.type === 'textfield')}
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
                            name="component"
                            value={birthDate}
                            onChange={onFieldChange}
                            filter={(comp) => (comp.type === 'date')}
                        />
                    </Field>
                </FormRow>
            </Fieldset>

        </ComponentsContext.Provider>
    )
};

FormLogic.propTypes = {
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
};


export default Appointments;
