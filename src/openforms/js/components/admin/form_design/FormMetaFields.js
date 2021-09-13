/*
global URLify;
 */
import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import Select from '../forms/Select';
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
        publicName,
        internalName,
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
                    label={<FormattedMessage defaultMessage="ID" description="Form ID field label" />}
                    helpText={<FormattedMessage defaultMessage="Unique identifier for the form" description="Form ID field help text" />}
                    errors={errors.uuid}
                    required
                >
                    <TextInput value={uuid} onChange={onChange} disabled={true}/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.publicName"
                    label={<FormattedMessage defaultMessage="Public name" description="Form public name field label" />}
                    helpText={<FormattedMessage defaultMessage="Public name/title of the form" description="Form public name field help text" />}
                    errors={errors.name}
                    required
                >
                    <TextInput value={publicName} onChange={onChange} onBlur={setFormSlug} />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.internalName"
                    label={<FormattedMessage defaultMessage="Internal name" description="Form name field label" />}
                    helpText={<FormattedMessage defaultMessage="Internal name/title of the form" description="Form name field help text" />}
                    errors={errors.name}
                >
                    <TextInput value={internalName} onChange={onChange} onBlur={setFormSlug} />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.slug"
                    label={<FormattedMessage defaultMessage="Slug" description="Form slug field label" />}
                    helpText={<FormattedMessage defaultMessage="Slug of the form, used in URLs" description="Form slug field help text" />}
                    errors={errors.slug}
                    required
                >
                    <TextInput value={slug} onChange={onChange} />
                </Field>
            </FormRow>

            <FormRow>
                <AuthPluginField
                    availableAuthPlugins={availableAuthPlugins}
                    selectedAuthPlugins={selectedAuthPlugins}
                    onChange={onAuthPluginChange}
                    errors={errors.authPlugins}
                />
            </FormRow>

            <FormRow>
                <Checkbox
                    name="form.showProgressIndicator"
                    label={<FormattedMessage defaultMessage="Show progress indicator" description="Progress indicator field label" />}
                    helpText={<FormattedMessage defaultMessage="Whether the step progression should be displayed in the UI or not." description="Progress indicator help text" />}
                    checked={showProgressIndicator}
                    errors={errors.showProgressIndicator}
                    onChange={(event) => onCheckboxChange(event, showProgressIndicator)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.active"
                    label={<FormattedMessage defaultMessage="Active" description="Form active field label" />}
                    helpText={<FormattedMessage defaultMessage="Whether the form is active or not. Deactivated forms cannot be started." description="Form active field help text" />}
                    checked={active}
                    errors={errors.active}
                    onChange={(event) => onCheckboxChange(event, active)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.isDeleted"
                    label={<FormattedMessage defaultMessage="Is deleted" description="Form deleted field label" />}
                    helpText={<FormattedMessage defaultMessage="Whether the form is (soft) deleted" description="Form deleted field help text" />}
                    checked={isDeleted}
                    errors={errors.isDeleted}
                    onChange={(event) => onCheckboxChange(event, isDeleted)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.maintenanceMode"
                    label={<FormattedMessage defaultMessage="Maintenance mode" description="Form maintenance mode field label" />}
                    helpText={<FormattedMessage defaultMessage="Users will not be able to start the form if it is in maintenance mode." description="Form maintenance mode field help text" />}
                    checked={maintenanceMode}
                    errors={errors.maintenanceMode}
                    onChange={(event) => onCheckboxChange(event, maintenanceMode)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.canSubmit"
                    label={<FormattedMessage defaultMessage="Submit button enabled" description="Form canSubmit field label" />}
                    helpText={<FormattedMessage defaultMessage="If checked, the user can submit the form. Uncheck this for 'decision' trees." description="Form canSubmit field help text" />}
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
        publicName: PropTypes.string.isRequired,
        internalName: PropTypes.string,
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
    availableAuthPlugins: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        label: PropTypes.string,
        providesAuth: PropTypes.arrayOf(PropTypes.string)
    })),
    selectedAuthPlugins: PropTypes.array.isRequired,
    onAuthPluginChange: PropTypes.func.isRequired,
};


export default FormMetaFields;
