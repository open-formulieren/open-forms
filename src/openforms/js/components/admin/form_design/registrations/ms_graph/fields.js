import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

export const FolderPath = () => {
  const [fieldProps] = useField('folderPath');
  return (
    <FormRow>
      <Field
        name="folderPath"
        label={
          <FormattedMessage
            description="MS Graph registration options 'folderPath' label"
            defaultMessage="Folder path"
          />
        }
        helpText={
          <FormattedMessage
            description="MS Graph registration options 'folderPath' help text"
            defaultMessage={` The path of the folder where folders containing Open-Forms related
              documents will be created. You can use the expressions
              <code>'{{' year '}}'</code>, <code>'{{' month '}}'</code> and
              <code>'{{' day '}}'</code>. The path must start with <code>/</code>.
            `}
            values={{
              code: chunks => <code>{chunks}</code>,
            }}
          />
        }
      >
        <TextInput id="id_folderPath" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

export const DriveID = () => {
  const [fieldProps] = useField('driveId');
  return (
    <FormRow>
      <Field
        name="driveId"
        label={
          <FormattedMessage
            description="MS Graph registration options 'driveId' label"
            defaultMessage="Drive ID"
          />
        }
        helpText={
          <FormattedMessage
            description="MS Graph registration options 'driveId' help text"
            defaultMessage="ID of the drive to use. If left empty, the default drive will be used."
          />
        }
      >
        <TextInput id="id_driveId" {...fieldProps} />
      </Field>
    </FormRow>
  );
};
