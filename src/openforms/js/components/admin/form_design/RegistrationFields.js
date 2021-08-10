import React, {useState} from 'react';
import PropTypes from 'prop-types';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from "../forms/Select";
import {TextInput} from '../forms/Inputs';


const RegistrationFields = ({
    backends=[],
    selectedBackend='',
    backendOptions={},
    onChange,
}) => {
    const backendChoices = backends.map( backend => [backend.id, backend.label]);

    // TODO: proper UI, this doesn't work
    const onBackendOptionsChange = (event) => {
        // transform string value back into object
        const {name, value} = event.target;
        let parsedValue;
        try {
            parsedValue = JSON.parse(value);
        } catch (err) {
            parsedValue = backendOptions;
        }
        const fakeEvent = {target: {name, value: parsedValue}};
        onChange(fakeEvent);
    };

    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="form.registrationBackend"
                    label="Select registration backend"
                >
                    <Select
                        name="Registration backend"
                        choices={backendChoices}
                        value={selectedBackend}
                        onChange={onChange}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.registrationBackendOptions"
                    label="Registration Backend Options"
                >
                    <TextInput
                        value={JSON.stringify(backendOptions || {})}
                        onChange={onBackendOptionsChange}
                        maxLength="1000" />
                </Field>
            </FormRow>
        </Fieldset>
    );
};

RegistrationFields.propTypes = {
    backends: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
    })),
    selectedBackend: PropTypes.string,
    backendOptions: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default RegistrationFields;
