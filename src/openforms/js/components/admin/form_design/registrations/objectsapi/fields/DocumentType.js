import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const DocumentType = ({name, label, helpText}) => {
  const [fieldProps] = useField(name);
  return (
    <FormRow>
      <Field name={name} label={label} helpText={helpText}>
        <TextInput id={`id_${name}`} {...fieldProps} />
      </Field>
    </FormRow>
  );
};

DocumentType.propTypes = {
  name: PropTypes.oneOf([
    'informatieobjecttypeSubmissionReport',
    'informatieobjecttypeSubmissionCsv',
    'informatieobjecttypeAttachment',
  ]).isRequired,
  label: PropTypes.node.isRequired,
  helpText: PropTypes.node,
};

const InformatieobjecttypeSubmissionReport = () => (
  <DocumentType
    name="informatieobjecttypeSubmissionReport"
    label={
      <FormattedMessage
        description='Objects API registration options "Submission report PDF informatieobjecttype" label'
        defaultMessage="Submission report PDF informatieobjecttype"
      />
    }
    helpText={
      <FormattedMessage
        description='Objects API registration options "Submission report PDF informatieobjecttype" description'
        defaultMessage="URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission report PDF"
      />
    }
  />
);

const InformatieobjecttypeSubmissionCsv = () => (
  <DocumentType
    name="informatieobjecttypeSubmissionCsv"
    label={
      <FormattedMessage
        description='Objects API registration options "Submission report CSV informatieobjecttype" label'
        defaultMessage="Submission report CSV informatieobjecttype"
      />
    }
    helpText={
      <FormattedMessage
        description='Objects API registration options "Submission report CSV informatieobjecttype" description'
        defaultMessage="URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission report CSV"
      />
    }
  />
);

const InformatieobjecttypeAttachment = () => (
  <DocumentType
    name="informatieobjecttypeAttachment"
    label={
      <FormattedMessage
        description='Objects API registration options "Attachment informatieobjecttype" label'
        defaultMessage="Attachment informatieobjecttype"
      />
    }
    helpText={
      <FormattedMessage
        description='Objects API registration options "Attachment informatieobjecttype" description'
        defaultMessage="URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission attachments"
      />
    }
  />
);

export const DocumentTypesFieldet = () => (
  <Fieldset
    title={
      <FormattedMessage
        description="Objects registration: document types"
        defaultMessage="Document types"
      />
    }
    collapsible
    fieldNames={[
      'informatieobjecttypeSubmissionReport',
      'informatieobjecttypeSubmissionCsv',
      'informatieobjecttypeAttachment',
    ]}
  >
    <InformatieobjecttypeSubmissionReport />
    <InformatieobjecttypeSubmissionCsv />
    <InformatieobjecttypeAttachment />
  </Fieldset>
);
