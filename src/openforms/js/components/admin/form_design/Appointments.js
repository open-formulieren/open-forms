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

    const [state, dispatch] = useImmerReducer(reducer, {...initialState});

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

    // rendering logic
    const {
        products,
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
        </ComponentsContext.Provider>
    )
};

FormLogic.propTypes = {
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
};


export default Appointments;
