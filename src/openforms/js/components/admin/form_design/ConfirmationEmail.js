import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, FormattedMessage, useIntl} from 'react-intl';
import TinyMCEEditor from './Editor';
import FormRow from '../forms/FormRow';
import Field from '../forms/Field';
import Fieldset from '../forms/Fieldset';
import {Checkbox, TextInput} from '../forms/Inputs';
import {getTranslatedChoices} from "../../../utils/i18n";
import Select from "../forms/Select";


const CONFIRMATION_EMAIL_OPTIONS = [
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


const ConfirmationEmail = ({ confirmationEmailOption='global_email', template={}, onChange }) => {
    const intl = useIntl();
    const confirmationEmailOptions = getTranslatedChoices(intl, CONFIRMATION_EMAIL_OPTIONS);

    const { subject, content } = template;

    const onCheckboxChange = (event, currentValue) => {
        const { target: {name} } = event;
        onChange({target: {name, value: !currentValue}});
    };

    return (
        <Fieldset title={<FormattedMessage defaultMessage="Submission confirmation email template"
                                           description="Submission confirmation email fieldset title"/>}>
            <FormRow>
                <Field
                    name="form.confirmationEmailTemplate.subject"
                    label={<FormattedMessage defaultMessage="Confirmation Email Subject" description="Confirmation Email Subject label" />}
                >
                    <TextInput value={subject} onChange={onChange} maxLength="1000"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.confirmationEmailTemplate.content"
                    label={<FormattedMessage defaultMessage="Confirmation Email Content"
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
                    name="form.confirmationEmail"
                    label={<FormattedMessage defaultMessage="Confirmation Email"
                                             description="Form confirmation email label"/>}
                    helpText={<FormattedMessage
                        defaultMessage="Will send the email specified."
                        description="Form confirmation email help text"/>}
                >
                    <Select
                        name="form.confirmationEmail"
                        choices={confirmationEmailOptions}
                        value={confirmationEmailOption}
                        onChange={onChange}
                    />
                </Field>



            </FormRow>
        </Fieldset>
    );
};

ConfirmationEmail.propTypes = {
    confirmationEmailOption: PropTypes.string,
    template: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default ConfirmationEmail;
