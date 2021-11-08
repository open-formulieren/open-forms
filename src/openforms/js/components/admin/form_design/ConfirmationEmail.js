import {FormattedMessage} from "react-intl";
import React from "react";
import FormRow from "../forms/FormRow";
import Field from "../forms/Field";
import TinyMCEEditor from "./Editor";
import Fieldset from "../forms/Fieldset";
import PropTypes from "prop-types";

const ConfirmationEmail = ({ shouldSend=false, template={} }) => {

    const { subject, content } = template;

    return (
        <Fieldset title={<FormattedMessage defaultMessage="Submission confirmation email template"
                                           description="Submission confirmation email fieldset title"/>}>
            <FormRow>
                <Field
                    name="form.submissionConfirmationEmailTemplate"
                    label={<FormattedMessage defaultMessage="Submission page content"
                                             description="Confirmation template label"/>}
                    helpText={
                        <FormattedMessage
                            defaultMessage="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data. If not specified, the global template will be used."
                            description="Confirmation template help text"
                        />
                    }
                >
                    <TinyMCEEditor
                        content={content}
                        onEditorChange={(newValue, editor) => onFieldChange(
                            {target: {name: 'form.submissionConfirmationEmailTemplate', value: newValue}}
                        )}
                    />
                </Field>
            </FormRow>
        </Fieldset>
    );
};

ConfirmationEmail.propTypes = {
    shouldSend: PropTypes.bool,
    template: PropTypes.object,
};


export default ConfirmationEmail;
