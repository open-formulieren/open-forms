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


const RelativeAPIEndpoint = () => {
  // TODO-4098: is this the serializer name?
  const [fieldProps] = useField('relativeApiEndpoint');
  return (
    <FormRow>
      <Field
        name="relativeApiEndpoint"
        label={
          <FormattedMessage
            description="JSON registration options 'relativeApiEndpoint' label"
            defaultMessage="Relative API Endpoint"
          />
        }
      >
        <TextInput id="id_relativeApiEndpoint" {...fieldProps} />
      </Field>
    </FormRow>
  );
};


const JSONOptionsForm = ({name, label, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);
  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={relevantErrors.length}
      modalTitle={
        <FormattedMessage
          description="JSON registration options modal title"
          defaultMessage="Plugin configuration: JSON"
        />
      }
      initialFormData={{relativeApiEndpoint: '', ...formData}}
      onSubmit={values => onChange({formData: values})}
      modalSize="small"
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <RelativeAPIEndpoint />
        </Fieldset>
      </ValidationErrorsProvider>
    </ModalOptionsConfiguration>
  );
};

JSONOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  formData: PropTypes.shape({
    apiEndpoint: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default JSONOptionsForm;
