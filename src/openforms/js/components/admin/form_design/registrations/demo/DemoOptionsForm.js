import {useField} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

const ExtraLine = () => {
  const [fieldProps] = useField('extraLine');
  return (
    <FormRow>
      <Field
        name="extraLine"
        label={
          <FormattedMessage
            description="Demo registration options 'extraLine' label"
            defaultMessage="Extra print statement"
          />
        }
      >
        <TextInput id="id_extraLine" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

const DemoOptionsForm = ({name, label, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <ModalOptionsConfiguration
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
      modalSize="small"
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <ExtraLine />
        </Fieldset>
      </ValidationErrorsProvider>
    </ModalOptionsConfiguration>
  );
};

DemoOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  formData: PropTypes.shape({
    extraLine: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default DemoOptionsForm;
