import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

import {DriveID, FolderPath} from './fields';

const MSGraphOptionsForm = ({name, label, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={relevantErrors.length}
      modalTitle={
        <FormattedMessage
          description="MS Graph registration options modal title"
          defaultMessage="Plugin configuration: MS Graph"
        />
      }
      initialFormData={{folderPath: '', driveId: '', ...formData}}
      onSubmit={values => onChange({formData: values})}
      modalSize=""
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <FolderPath />
          <DriveID />
        </Fieldset>
      </ValidationErrorsProvider>
    </ModalOptionsConfiguration>
  );
};

MSGraphOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  formData: PropTypes.shape({
    folderPath: PropTypes.string,
    driveId: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default MSGraphOptionsForm;
