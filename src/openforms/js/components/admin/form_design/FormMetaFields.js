/*
global URLify;
 */
import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, FormattedMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../utils/i18n';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import {TextInput, Checkbox} from '../forms/Inputs';
import Select from '../forms/Select';
import AuthPluginField from './AuthPluginField';
import TinyMCEEditor from './Editor';
import AuthPluginAutoLoginField from './AuthPluginAutoLoginField';


export const SUMBISSION_ALLOWED_CHOICES = [
    [
        'yes',
        defineMessage({
            description: 'option "yes" of "submission_allowed"',
            defaultMessage: 'Yes',
        })
    ],
    [
        'no_with_overview',
        defineMessage({
            description: 'option "no_with_overview" of "submission_allowed"',
            defaultMessage: 'No (with overview page)',
        })
    ],
    [
        'no_without_overview',
        defineMessage({
            description: 'option "no_without_overview" of "submission_allowed"',
            defaultMessage: 'No (without overview page)',
        })
    ],
];


/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormMetaFields = ({
    form,
    onChange,
    availableAuthPlugins,
    selectedAuthPlugins,
    onAuthPluginChange,
}) => {
    const {
        uuid,
        name,
        internalName,
        slug,
        showProgressIndicator,
        active,
        isDeleted,
        maintenanceMode,
        submissionAllowed,
        explanationTemplate,
    } = form;

    const intl = useIntl();

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
                    required
                >
                    <TextInput value={uuid} onChange={onChange} disabled={true}/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.name"
                    label={<FormattedMessage defaultMessage="Name" description="Form name field label" />}
                    helpText={<FormattedMessage defaultMessage="Name/title of the form" description="Form name field help text" />}
                    required
                >
                    <TextInput value={name} onChange={onChange} onBlur={setFormSlug} maxLength="150"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.internalName"
                    label={<FormattedMessage defaultMessage="Internal name" description="Form name field label" />}
                    helpText={<FormattedMessage defaultMessage="Internal name/title of the form" description="Form name field help text" />}
                >
                    <TextInput value={internalName} onChange={onChange} maxLength="150"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.slug"
                    label={<FormattedMessage defaultMessage="Slug" description="Form slug field label" />}
                    helpText={<FormattedMessage defaultMessage="Slug of the form, used in URLs" description="Form slug field help text" />}
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
                />
            </FormRow>

            <FormRow>
                <Field
                    name="form.autoLoginAuthenticationBackend"
                    label={
                        <FormattedMessage
                            defaultMessage="Authentication automatic login"
                            description="Auto-login field label"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            defaultMessage="Select which authentication backend is automatically redirected to."
                            description="Auto-login field help text"
                        />
                    }
                >
                    <AuthPluginAutoLoginField
                        eligiblePlugins={availableAuthPlugins.filter(plugin => selectedAuthPlugins.includes(plugin.id))}
                        value={form.autoLoginAuthenticationBackend}
                        onChange={onChange}
                    ></AuthPluginAutoLoginField>
                </Field>
            </FormRow>

            <FormRow>
                <Checkbox
                    name="form.showProgressIndicator"
                    label={<FormattedMessage defaultMessage="Show progress indicator" description="Progress indicator field label" />}
                    helpText={<FormattedMessage defaultMessage="Whether the step progression should be displayed in the UI or not." description="Progress indicator help text" />}
                    checked={showProgressIndicator}
                    onChange={(event) => onCheckboxChange(event, showProgressIndicator)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.active"
                    label={<FormattedMessage defaultMessage="Active" description="Form active field label" />}
                    helpText={<FormattedMessage defaultMessage="Whether the form is active or not. Deactivated forms cannot be started." description="Form active field help text" />}
                    checked={active}
                    onChange={(event) => onCheckboxChange(event, active)}

                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.isDeleted"
                    label={<FormattedMessage defaultMessage="Is deleted" description="Form deleted field label" />}
                    helpText={<FormattedMessage defaultMessage="Whether the form is (soft) deleted" description="Form deleted field help text" />}
                    checked={isDeleted}
                    onChange={(event) => onCheckboxChange(event, isDeleted)}
                />
            </FormRow>
            <FormRow>
                <Checkbox
                    name="form.maintenanceMode"
                    label={<FormattedMessage defaultMessage="Maintenance mode" description="Form maintenance mode field label" />}
                    helpText={<FormattedMessage defaultMessage="Users will not be able to start the form if it is in maintenance mode." description="Form maintenance mode field help text" />}
                    checked={maintenanceMode}
                    onChange={(event) => onCheckboxChange(event, maintenanceMode)}
                />
            </FormRow>
            <FormRow>
                <Field
                    name="form.submissionAllowed"
                    label={
                        <FormattedMessage
                            defaultMessage="Submission allowed"
                            description="Form submissionAllowed field label"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            defaultMessage="Whether the user is allowed to submit this form or not, and whether the overview page should be shown if they are not."
                            description="Form submissionAllowed field help text"
                        />
                    }
                >
                    <Select
                        choices={getTranslatedChoices(intl, SUMBISSION_ALLOWED_CHOICES)}
                        value={submissionAllowed}
                        onChange={onChange}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.explanationTemplate"
                    label={<FormattedMessage defaultMessage="Explanation template" description="Start page explanation text label" />}
                    helpText={
                        <FormattedMessage
                            defaultMessage="Content that will be shown on the start page of the form, below the title and above the log in text."
                            description="Start page explanation text"
                        />
                    }
                >
                    <TinyMCEEditor
                        content={explanationTemplate}
                        onEditorChange={(newValue, editor) => onChange(
                            {target: {name: 'form.explanationTemplate', value: newValue}}
                        )}
                    />
                </Field>
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
    availableAuthPlugins: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        label: PropTypes.string,
        providesAuth: PropTypes.arrayOf(PropTypes.string)
    })),
    selectedAuthPlugins: PropTypes.array.isRequired,
    onAuthPluginChange: PropTypes.func.isRequired,
};


export default FormMetaFields;
