import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Fieldset from 'components/admin/forms/Fieldset';
import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';
import {getChoicesFromSchema} from 'utils/json-schema';

import {FormVariablesSelect, Path, ServiceSelect} from './fields';

const JSONDumpOptionsForm = ({name, label, schema, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  // Get form variables and create form variable options
  const formContext = useContext(FormContext);
  const formVariables = formContext.formVariables ?? [];
  const staticVariables = formContext.staticVariables ?? [];
  const allFormVariables = staticVariables.concat(formVariables);

  const formVariableOptions = [];
  for (const formVariable of allFormVariables) {
    formVariableOptions.push({value: formVariable.key, label: formVariable.name});
  }

  // Create service options
  const {service} = schema.properties;
  const serviceOptions = getChoicesFromSchema(service.enum, service.enumNames).map(
    ([value, label]) => ({value, label})
  );

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
      initialFormData={{
        service: null,
        path: '',
        formVariables: [],
        ...formData,
      }}
      onSubmit={values => onChange({formData: values})}
      modalSize="medium"
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <ServiceSelect options={serviceOptions} />
          <Path />
          <FormVariablesSelect options={formVariableOptions} />
        </Fieldset>
      </ValidationErrorsProvider>
    </ModalOptionsConfiguration>
  );
};

JSONDumpOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    properties: PropTypes.shape({
      service: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.number).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }).isRequired,
  }).isRequired,
  formData: PropTypes.shape({
    service: PropTypes.number,
    path: PropTypes.string,
    // TODO-4908: might need to rename this to selectedFormVariables to avoid confusion or even
    //  naming conflicts
    formVariables: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
};

export default JSONDumpOptionsForm;
