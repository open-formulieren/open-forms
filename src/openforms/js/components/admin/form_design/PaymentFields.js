import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from "../forms/Select";
import Form from "@rjsf/core";


const PaymentFields = ({
    backends=[],
    selectedBackend='',
    backendOptions={},
    onChange
}) => {
    const backendChoices = backends.map( backend => [backend.id, backend.label]);
    const backend = backends.find( backend => backend.id === selectedBackend );
    const hasOptionsForm = Boolean(backend && Object.keys(backend.schema.properties).length);

    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="form.paymentBackend"
                    label={<FormattedMessage description="Payment backend label" defaultMessage="Select payment backend" />}
                >
                    <Select
                        choices={backendChoices}
                        value={selectedBackend}
                        onChange={ (event) => {
                            onChange(event);
                            // Clear options when changing backend
                            onChange({target: {name: 'form.paymentBackendOptions', value: {}}})
                        }}
                        allowBlank
                    />
                </Field>
            </FormRow>

            {
                hasOptionsForm
                ? (
                    <FormRow>
                        <Field
                            name="form.paymentBackendOptions"
                            label={<FormattedMessage description="Payment backend options label" defaultMessage="Payment backend options" />}
                        >
                            <Form
                                schema={backend.schema}
                                formData={backendOptions}
                                onChange={({ formData }) => onChange({target: {name: 'form.paymentBackendOptions', value: formData}})}
                                children={true}
                            />
                        </Field>
                    </FormRow>
                )
                : null
            }

        </Fieldset>
    );
};

PaymentFields.propTypes = {
    backends: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
        schema: PropTypes.shape({
            type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
            properties: PropTypes.object,
            required: PropTypes.arrayOf(PropTypes.string),
        }),
    })),
    selectedBackend: PropTypes.string,
    backendOptions: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default PaymentFields;
