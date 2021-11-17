import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, FormattedMessage, useIntl} from 'react-intl';
import TinyMCEEditor from './Editor';
import FormRow from '../forms/FormRow';
import Field from '../forms/Field';
import Fieldset from '../forms/Fieldset';
import {TextInput} from '../forms/Inputs';
import {getTranslatedChoices} from "../../../utils/i18n";
import Select from "../forms/Select";


const EMAIL_OPTIONS = [
    [
        'global_email',
        defineMessage({
            description: 'global_email option label',
            defaultMessage: 'Global email',
        })
    ],
    [
        'form_specific_email',
        defineMessage({
            description: 'form_specific_email option label',
            defaultMessage: 'Form specific email',
        })
    ],
    [
        'no_email',
        defineMessage({
            description: 'no_email option label',
            defaultMessage: 'No email',
        })
    ],
];


const Confirmation = ({ pageTemplate='', emailOption='global_email', emailTemplate={}, onChange }) => {
    const intl = useIntl();
    const emailOptions = getTranslatedChoices(intl, EMAIL_OPTIONS);

    const { subject, content } = emailTemplate;

    return (
        <>
            <Fieldset title={<FormattedMessage defaultMessage="Submission confirmation template" description="Submission confirmation fieldset title" />}>
                <FormRow>
                    <Field
                        name="form.submissionConfirmationTemplate"
                        label={<FormattedMessage defaultMessage="Page content" description="Confirmation page content label" />}
                        helpText={
                            <FormattedMessage
                                defaultMessage="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data. If not specified, the global template will be used."
                                description="Confirmation template help text"
                            />
                        }
                    >
                        <TinyMCEEditor
                            content={pageTemplate}
                            onEditorChange={(newValue, editor) => onChange(
                                {target: {name: 'form.submissionConfirmationTemplate', value: newValue}}
                            )}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset title={<FormattedMessage defaultMessage="Submission confirmation email template"
                                               description="Submission confirmation email fieldset title"/>}>
                <FormRow>
                    <Field
                        name="form.confirmationEmailTemplate.subject"
                        label={<FormattedMessage defaultMessage="Subject" description="Confirmation Email Subject label" />}
                    >
                        <TextInput value={subject || ""} onChange={onChange} maxLength="1000"/>
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name="form.confirmationEmailTemplate.content"
                        label={<FormattedMessage defaultMessage="Content"
                                                 description="Confirmation Email Content label"/>}
                    >
                        <TinyMCEEditor
                            content={content}
                            onEditorChange={(newValue, editor) => onChange(
                                {target: {name: 'form.confirmationEmailTemplate.content', value: newValue}}
                            )}
                        />
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name="form.confirmationEmailOption"
                        label={<FormattedMessage defaultMessage="Email option"
                                                 description="Form confirmation email label"/>}
                        helpText={<FormattedMessage
                            defaultMessage="Will send the email specified."
                            description="Form confirmation email help text"/>}
                    >
                        <Select
                            name="form.confirmationEmailOption"
                            choices={emailOptions}
                            value={emailOption}
                            onChange={onChange}
                        />
                    </Field>
                </FormRow>
            </Fieldset>
        </>
    );
};

Confirmation.propTypes = {
    pageTemplate: PropTypes.string,
    emailOption: PropTypes.string,
    emailTemplate: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default Confirmation;
