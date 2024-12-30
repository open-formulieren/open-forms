import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';

import EmailOptionsFormFields from './EmailOptionsFormFields';

const EmailOptionsForm = ({name, label, schema, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="Email registration options modal title"
          defaultMessage="Plugin configuration: Email"
        />
      }
      initialFormData={{
        toEmailsFromVariable: '', // ensure an initial value is provided
        ...formData,
        // ensure we have a blank row initially
        toEmails: formData.toEmails?.length ? formData.toEmails : [''],
      }}
      onSubmit={values => onChange({formData: values})}
    >
      <EmailOptionsFormFields name={name} schema={schema} />
    </ModalOptionsConfiguration>
  );
};

EmailOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']),
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  formData: PropTypes.shape({
    attachFilesToEmail: PropTypes.bool,
    attachmentFormats: PropTypes.arrayOf(PropTypes.string),
    emailContentTemplateHtml: PropTypes.string,
    emailContentTemplateText: PropTypes.string,
    emailPaymentSubject: PropTypes.string,
    emailSubject: PropTypes.string,
    paymentEmails: PropTypes.arrayOf(PropTypes.string),
    toEmails: PropTypes.arrayOf(PropTypes.string),
    toEmailsFromVariable: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default EmailOptionsForm;
