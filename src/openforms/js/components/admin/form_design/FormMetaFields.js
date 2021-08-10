/*
global URLify;
 */
import React from 'react';
import PropTypes from 'prop-types';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from "../forms/Select";
import {TextInput, Checkbox} from '../forms/Inputs';
import AuthPluginField from './AuthPluginField';


/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormMetaFields = ({
    form,
    onChange,
    errors={},
    availableAuthPlugins,
    selectedAuthPlugins,
    onAuthPluginChange
}) => {
    const {
        uuid,
        name,
        slug,
        showProgressIndicator,
        active,
        isDeleted,
        maintenanceMode,
        canSubmit
    } = form;

    const onCheckboxChange = (event, currentValue) => {
        const { target: {name} } = event;
        onChange({target: {name, value: !currentValue}});
    };

    const setFormSlug = (event) => {
        // do nothing if there's already a slug set
        if (slug) return;

        // sort-of taken from Django's jquery prepopulate module
        const newSlug = URLify(event.target.value, 100, false);
        onChange({
            target: {
                name: 'form.slug',
                value: newSlug,
            }
        });
    };

    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="form.uuid"
                    label="Form UUID"
                    helpText="Unique identifier for the form"
                    errors={errors.uuid}
                    required
                >
                    <TextInput value={uuid} onChange={onChange} disabled={true}/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.name"
                    label="Form name"
                    helpText="Name of the form"
                    errors={errors.name}
                    required
                >
                    <TextInput value={name} onChange={onChange} onBlur={setFormSlug} />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.slug"
                    label="Form slug"
                    helpText="Slug of the form"
                    errors={errors.slug}
                    required
                >
                    <TextInput value={slug} onChange={onChange} />
                </Field>
            </FormRow>

            <FormRow>
                <AuthPluginField
                    loading={availableAuthPlugins.loading}
                    availableAuthPlugins={availableAuthPlugins.data}
                    selectedAuthPlugins={selectedAuthPlugins}
                    onChange={onAuthPluginChange}
                    errors={errors.authPlugins}
                />
            </FormRow>

            <FormRow>
                <Checkbox
                    name="form.showProgressIndicator"
                    label="Show progress indicator"
                    helpText="Whether the step progression should be displayed in the UI or not."
                    checked={showProgressIndicator}
                    errors={errors.showProgressIndicator}
                    onChange={(event) => onCheckboxChange(event, showProgressIndicator)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.active"
                    label="Active"
                    helpText="Whether the form is active or not"
                    checked={active}
                    errors={errors.active}
                    onChange={(event) => onCheckboxChange(event, active)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.isDeleted"
                    label="Is deleted"
                    helpText="Whether the form is (soft) deleted"
                    checked={isDeleted}
                    errors={errors.isDeleted}
                    onChange={(event) => onCheckboxChange(event, isDeleted)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.maintenanceMode"
                    label="Maintenance mode"
                    helpText="Users will not be able to start the form if it is in maintenance mode."
                    checked={maintenanceMode}
                    errors={errors.maintenanceMode}
                    onChange={(event) => onCheckboxChange(event, maintenanceMode)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.canSubmit"
                    label="Can submit"
                    helpText="Can the user submit the form?"
                    checked={canSubmit}
                    errors={errors.canSubmit}
                    onChange={(event) => onCheckboxChange(event, canSubmit)}
                />
            </FormRow>
        </Fieldset>
    );
};

FormMetaFields.propTypes = {
    form: PropTypes.shape({
        name: PropTypes.string.isRequired,
        uuid: PropTypes.string.isRequired,
        slug: PropTypes.string.isRequired,
        showProgressIndicator: PropTypes.bool.isRequired,
        active: PropTypes.bool.isRequired,
        isDeleted: PropTypes.bool.isRequired,
        maintenanceMode: PropTypes.bool.isRequired,
        submissionConfirmationTemplate: PropTypes.string.isRequired,
        registrationBackend: PropTypes.string.isRequired,
        registrationBackendOptions: PropTypes.object,
    }).isRequired,
    onChange: PropTypes.func.isRequired,
    errors: PropTypes.object,
    availableAuthPlugins: PropTypes.shape({
        loading: PropTypes.bool.isRequired,
        data: PropTypes.object.isRequired,
    }).isRequired,
    selectedAuthPlugins: PropTypes.array.isRequired,
    onAuthPluginChange: PropTypes.func.isRequired,
};


export default FormMetaFields;
