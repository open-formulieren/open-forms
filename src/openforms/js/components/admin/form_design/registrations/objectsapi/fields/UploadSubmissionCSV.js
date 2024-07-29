import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const UploadSubmissionCsv = () => {
  const [fieldProps] = useField({name: 'uploadSubmissionCsv', type: 'checkbox'});
  return (
    <FormRow>
      <Checkbox
        id="id_uploadSubmissionCsv"
        label={
          <FormattedMessage
            description="Objects API registration: uploadSubmissionCsv label"
            defaultMessage="Upload submission CSV"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration: uploadSubmissionCsv helpText"
            defaultMessage="Indicates whether or not the submission CSV should be uploaded as a Document in Documenten API and attached to the product request."
          />
        }
        {...fieldProps}
      />
    </FormRow>
  );
};

export default UploadSubmissionCsv;
