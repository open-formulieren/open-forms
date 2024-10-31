import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import OptionsConfiguration from 'components/admin/form_design/registrations/shared/OptionsConfiguration';
import {filterErrors} from 'components/admin/form_design/registrations/shared/utils';
import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
} from 'components/admin/forms/ValidationErrors';

import {DriveID, FolderPath} from './fields';

const MSGraphOptionsForm = ({name, label, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <OptionsConfiguration
      name={name}
      label={label}
      numErrors={relevantErrors.length}
      modalTitle={
        <FormattedMessage
          description="Demo registration options modal title"
          defaultMessage="Plugin configuration: demo"
        />
      }
      initialFormData={{extraLine: '', ...formData}}
      onSubmit={values => onChange({formData: values})}
      modalSize=""
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <FolderPath />
          <DriveID />
        </Fieldset>
      </ValidationErrorsProvider>
    </OptionsConfiguration>
  );
};

MSGraphOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  formData: PropTypes.shape({
    extraLine: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default MSGraphOptionsForm;
