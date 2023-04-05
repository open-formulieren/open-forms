import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import {TextArea, TextInput} from 'components/admin/forms/Inputs';

import FormRow from '../../forms/FormRow';
import TinyMCEEditor from '../Editor';
import {BackendType} from './types';

const EmailRegistrationBackendConfigOverrides = ({onChange}) => {
  const {form} = useContext(FormContext);

  return (
    <Fieldset
      title={
        <FormattedMessage
          defaultMessage="Form specific registration email templates"
          description="Registration email template options label"
        />
      }
    >
      <FormRow>
        <Field
          name="form.registrationEmailSubject"
          label={
            <FormattedMessage
              defaultMessage="Registration email subject"
              description="Registration email subject name"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Overwrites the globally configured subject for the registration email."
              description="registration email subject help text"
            />
          }
        >
          <TextInput value={form.registrationEmailSubject} onChange={onChange} />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="form.registrationEmailPaymentSubject"
          label={
            <FormattedMessage
              defaultMessage="Registration email payment subject"
              description="Registration email payment subject name"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Overwrites the globally configured subject for the registration email sent after payment."
              description="registration email payment subject help text"
            />
          }
        >
          <TextInput value={form.registrationEmailPaymentSubject} onChange={onChange} />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="form.registrationEmailContentHtml"
          label={
            <FormattedMessage
              defaultMessage="Registration email content (HTML)"
              description="Registration email HTML content name"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Overwrites the globally configured HTML for the registration email."
              description="registration email HTML content help text"
            />
          }
        >
          <TinyMCEEditor
            content={form.registrationEmailContentHtml}
            onEditorChange={(newValue, editor) =>
              onChange({
                target: {
                  name: 'form.registrationEmailContentHtml',
                  value: newValue,
                },
              })
            }
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="form.registrationEmailContentText"
          label={
            <FormattedMessage
              defaultMessage="Registration email content (text)"
              description="Registration email text content name"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Overwrites the globally configured text for the registration email. This should contain the same information as the HTML template, in case the email client does not render the HTML."
              description="registration email text content help text"
            />
          }
        >
          <TextArea cols={50} value={form.registrationEmailContentText} onChange={onChange} />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

const GlobalConfigurationOverrides = ({backend, onChange}) => {
  switch (backend.id) {
    case 'email': {
      return <EmailRegistrationBackendConfigOverrides onChange={onChange} />;
    }
    default:
      return null;
  }
};

GlobalConfigurationOverrides.propTypes = {
  backend: BackendType.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default GlobalConfigurationOverrides;
