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
import {getChoicesFromSchema} from 'utils/json-schema';

import {
  AdditionalMetadataVariables,
  FixedMetadataVariables,
  Path,
  ServiceSelect,
  Variables,
} from './fields';

const JSONDumpOptionsForm = ({name, label, schema, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

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
        variables: [],
        fixedMetadataVariables: [],
        additionalMetadataVariables: [],
        ...formData,
      }}
      onSubmit={values => onChange({formData: values})}
      modalSize="large"
    >
      <ValidationErrorsProvider errors={relevantErrors}>
        <Fieldset>
          <ServiceSelect options={serviceOptions} />
          <Path />
          <Variables />
        </Fieldset>

        <Fieldset
          title={
            <FormattedMessage
              description="Metadata variables fieldset title"
              defaultMessage="Metadata variables"
            />
          }
          extraClassName="openforms-fieldset"
          collapsible
          initialCollapsed
        >
          <FixedMetadataVariables />
          <AdditionalMetadataVariables />
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
    variables: PropTypes.arrayOf(PropTypes.string),
    fixedMetadataVariables: PropTypes.arrayOf(PropTypes.string),
    additionalMetadataVariables: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
};

export default JSONDumpOptionsForm;
