import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from '../forms/Select';
import FormRjsfWrapper from '../RJSFWrapper';
import {BACKEND_OPTIONS_FORMS} from './registrations';


const BackendType = PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    schema: PropTypes.shape({
        type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
        properties: PropTypes.object,
        required: PropTypes.arrayOf(PropTypes.string),
    }),
});


const BackendOptionsFormRow = ({backend=null, currentOptions={}, onChange}) => {
    if (!backend) return null;

    const hasOptionsForm = Boolean(backend && Object.keys(backend.schema.properties).length);
    // either use the custom backend-specific defined form, or fall back to the generic react-json-schema-form
    const OptionsFormComponent = BACKEND_OPTIONS_FORMS[backend.id]?.form ?? FormRjsfWrapper;
    if (!hasOptionsForm && !BACKEND_OPTIONS_FORMS[backend.id]) {
        return null;
    }
    return (
        <FormRow>
            <OptionsFormComponent
                name="form.registrationBackendOptions"
                label={<FormattedMessage defaultMessage="Registration backend options" description="Registration backend options label" />}
                schema={backend.schema}
                formData={currentOptions}
                onChange={({ formData }) => onChange({target: {name: 'form.registrationBackendOptions', value: formData}})}
            />
        </FormRow>
    );
};

BackendOptionsFormRow.propTypes = {
    backend: BackendType,
    currentOptions: PropTypes.object,
    onChange: PropTypes.func.isRequired,
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
        <Fieldset
            style={{'--of-add-another-text': `"${addAnotherMsg}"`}}
            extraClassName="admin-fieldset"
        >
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

            <BackendOptionsFormRow backend={backend} currentOptions={backendOptions} onChange={onChange} />
        </Fieldset>
    );
};

RegistrationFields.propTypes = {
    backends: PropTypes.arrayOf(BackendType),
    selectedBackend: PropTypes.string,
    backendOptions: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default RegistrationFields;
