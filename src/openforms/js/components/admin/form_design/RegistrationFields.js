import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from "../forms/Select";
import {TextInput} from '../forms/Inputs';
import Form from "@rjsf/core";


const RegistrationFields = ({
    backends=[],
    selectedBackend='',
    backendOptions={},
    backendOptionsForms={},
    onChange,
}) => {
    const backendChoices = backends.map( backend => [backend.id, backend.label]);

    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="form.registrationBackend"
                    label={<FormattedMessage defaultMessage="Select registration backend" description="Registration backend label" />}
                >
                    <Select
                        name='Registration Method'
                        choices={backendChoices}
                        value={selectedBackend}
                        onChange={onChange}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.registrationBackendOptionsForm"
                    label="Registration Backend Options Form"
                >
                    {backendOptionsForms[selectedBackend] ?
                        <Form
                            schema={backendOptionsForms[selectedBackend]}
                            formData={backendOptions}
                            onChange={({ formData }) => {
                                onChange({target: {name: 'form.registrationBackendOptions', value: formData}});
                            }}
                            children={true}
                        />
                        :
                        <div> </div>
                    }
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
    backendOptionsForms: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default RegistrationFields;
