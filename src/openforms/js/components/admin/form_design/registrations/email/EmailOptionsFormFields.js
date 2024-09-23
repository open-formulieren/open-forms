import PropTypes from 'prop-types';
import {useContext} from 'react';

import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
} from 'components/admin/forms/ValidationErrors';

import EmailAttachmentFormatsSelect from './fields/EmailAttachmentFormatsSelect';
import EmailContentTemplateHTML from './fields/EmailContentTemplateHTML';
import EmailContentTemplateText from './fields/EmailContentTemplateText';
import EmailHasAttachmentSelect from './fields/EmailHasAttachmentSelect';
import EmailPaymentSubject from './fields/EmailPaymentSubject';
import EmailPaymentUpdateRecipients from './fields/EmailPaymentUpdateRecipients';
import EmailRecipients from './fields/EmailRecipients';
import EmailSubject from './fields/EmailSubject';
import {filterErrors, getChoicesFromSchema} from './utils';

const EmailOptionsFormFields = ({name, schema}) => {
  const validationErrors = useContext(ValidationErrorContext);

  const {attachFilesToEmail, attachmentFormats} = schema.properties;
  const attachFilesToEmailChoices = getChoicesFromSchema(
    attachFilesToEmail.enum,
    attachFilesToEmail.enumNames
  ).map(([value, label]) => ({value, label}));
  const attachmentFormatsChoices = getChoicesFromSchema(
    attachmentFormats.items.enum,
    attachmentFormats.items.enumNames
  ).map(([value, label]) => ({value, label}));

  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Fieldset>
        <EmailRecipients />
      </Fieldset>
      <Fieldset>
        <EmailAttachmentFormatsSelect options={attachmentFormatsChoices} />
      </Fieldset>
      <Fieldset>
        <EmailPaymentUpdateRecipients />
      </Fieldset>
      <Fieldset>
        <EmailHasAttachmentSelect options={attachFilesToEmailChoices} />

        <EmailSubject />
        <EmailPaymentSubject />

        <EmailContentTemplateHTML />
        <EmailContentTemplateText />
      </Fieldset>
    </ValidationErrorsProvider>
  );
};

EmailOptionsFormFields.propTypes = {
  name: PropTypes.string.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};

export default EmailOptionsFormFields;
