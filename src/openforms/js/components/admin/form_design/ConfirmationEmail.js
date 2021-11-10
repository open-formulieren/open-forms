import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import TinyMCEEditor from './Editor';
import FormRow from '../forms/FormRow';
import Field from '../forms/Field';
import Fieldset from '../forms/Fieldset';
import {Checkbox, TextInput} from '../forms/Inputs';

const ConfirmationEmail = ({ shouldSend=false, template={}, onChange }) => {

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
                <Checkbox
                    name="form.sendCustomConfirmationEmail"
                    label={<FormattedMessage defaultMessage="Should send custom confirmation email"
                                             description="Form send custom confirmation email label"/>}
                    helpText={<FormattedMessage
                        defaultMessage="Will send the email specified below.  If unchecked it will send the email specified in the global configuration"
                        description="Form send custom confirmation email help text"/>}
                    checked={shouldSend}
                    onChange={(event) => onCheckboxChange(event, shouldSend)}
                />
            </FormRow>
        </Fieldset>
    );
};

ConfirmationEmail.propTypes = {
    shouldSend: PropTypes.bool,
    template: PropTypes.object,
    onChange: PropTypes.func.isRequired,
};


export default ConfirmationEmail;
