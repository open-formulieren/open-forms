import React from 'react';
import ComponentSelection from './logic/ComponentSelection';
import {ComponentsContext} from './logic/Context';
import PropTypes from 'prop-types';
import {FormLogic} from './FormLogic';
import Field from '../forms/Field';
import {FormattedMessage} from 'react-intl';
import FormRow from '../forms/FormRow';
import Fieldset from "../forms/Fieldset";


const Appointments = ({ availableComponents={} }) => {
    return (
        <ComponentsContext.Provider value={availableComponents}>
            <Fieldset>
                <FormRow>
                    <Field
                        name="appointments.Products"
                        label={<FormattedMessage defaultMessage="Products Component" description="Products Component field label" />}
                        helpText={<FormattedMessage defaultMessage="Component where products for an appointment will be shown" description="Products Component field help text" />}
                    >
                        <ComponentSelection
                            name="component"
                            value=""
                            onChange={() => console.log('I changed')}
                            // Use below to filter on specific
                            // filter={(comp) => (comp.type === componentType)}
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
