import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import {WarningIcon} from 'components/admin/icons';

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

export const LegacyDocumentTypesFieldet = () => {
  const intl = useIntl();
  const {
    values: {
      catalogue,
      informatieobjecttypeSubmissionReport,
      informatieobjecttypeSubmissionCsv,
      informatieobjecttypeAttachment,
    },
  } = useFormikContext();

  const isConfigIgnored =
    catalogue &&
    (informatieobjecttypeSubmissionReport ||
      informatieobjecttypeSubmissionCsv ||
      informatieobjecttypeAttachment);

  return (
    <Fieldset
      title={
        <>
          {isConfigIgnored && (
            <WarningIcon
              asLead
              text={intl.formatMessage({
                description:
                  'Objects registration: warning that legacy document types will be ignored',
                defaultMessage:
                  'You have selected a catalogue - the document type URLs configured here will be ignored.',
              })}
            />
          )}
          <FormattedMessage
            description="Objects registration: document types (legacy)"
            defaultMessage="Document types (legacy)"
          />
        </>
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
};
