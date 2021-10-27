import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from '../forms/Select';
import Form from '@rjsf/core';

const FormRjsfWrapper = ({ name, label, schema, formData, onChange, errors }) => {
    let extraErrors = {};
    for (let [key, msg] of errors) {
        // The key is usually in the format form.field.rjsffield or form.field.rjsffield.index (in the case of an array field)
        const splitKey = key.split('.');
        // If there is no 'index' in the key, the <Field> component can handle displaying the errors
        if (splitKey.length < 4) continue;
        // Format errors for rjsf array fields
        if (schema.properties[splitKey[2]]) {
            if (!extraErrors[splitKey[2]]) extraErrors[splitKey[2]] = {};
            extraErrors[splitKey[2]][splitKey[3]] = {__errors: [msg]};
        }
    }

    return (
        <Field
            name={name}
            label={label}
            errors={extraErrors ?  [] : errors}
        >
            <Form
                schema={schema}
                formData={formData}
                onChange={onChange}
                children={true}
                extraErrors={extraErrors}
                showErrorList={false}
            />
        </Field>
    );
};


const RegistrationFields = ({
    backends=[],
    selectedBackend='',
    backendOptions={},
    onChange,
}) => {
    const intl = useIntl();

    const backendChoices = backends.map( backend => [backend.id, backend.label]);
    const backend = backends.find( backend => backend.id === selectedBackend );
    const hasOptionsForm = Boolean(backend && Object.keys(backend.schema.properties).length);

    const addAnotherMsg = intl.formatMessage({
        description: 'Button text to add extra item',
        defaultMessage: 'Add another',
    });

    return (
        <Fieldset style={{
            '--of-add-another-text': `"${addAnotherMsg}"`
        }}>
            <FormRow>
                <Field
                    name="form.registrationBackend"
                    label={<FormattedMessage defaultMessage="Select registration backend" description="Registration backend label" />}
                >
                    <Select
                        choices={backendChoices}
                        value={selectedBackend}
                        onChange={(event) => {
                            onChange(event);
                            // Clear options when changing backend
                            onChange({target: {name: 'form.registrationBackendOptions', value: {}}})
                        }}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
            {hasOptionsForm
                ? (<FormRow>
                    <FormRjsfWrapper
                        name="form.registrationBackendOptions"
                        label={<FormattedMessage defaultMessage="Registration backend options" description="Registration backend options label" />}
                        schema={backend.schema}
                        formData={backendOptions}
                        onChange={({ formData }) => onChange({target: {name: 'form.registrationBackendOptions', value: formData}})}
                    />
                </FormRow> )
                : null
            }
        </Fieldset>
    );
};

RegistrationFields.propTypes = {
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


export default RegistrationFields;
