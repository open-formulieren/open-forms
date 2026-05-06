import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';

import StufZDSOptionsFormFields from './StufZDSOptionsFormFields';

const normalizeFormData = formData => {
  return produce(formData, draft => {
    // ensure that the key serializeListToCsv is set for each mapping item
    const allVariableMappings = [...draft.variablesMapping, ...draft.variablesMappingInitiator];
    for (const mapping of allVariableMappings) {
      if (!('serializeListToCsv' in mapping)) {
        mapping.serializeListToCsv = false;
      }
    }
  });
};

const StufZDSOptionsForm = ({name, label, schema, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  const initialFormData = {
    // defaults
    zdsZaaktypeCode: '',
    zdsZaaktypeOmschrijving: '',
    zdsZaaktypeStatusCode: '',
    zdsZaaktypeStatusOmschrijving: '',
    zdsDocumenttypeOmschrijvingInzending: '',
    zdsZaakdocVertrouwelijkheid: '',
    variablesMapping: [],
    variablesMappingInitiator: [],
    // existing configuration
    ...formData,
  };
  const isNew = !Object.keys(formData).length;
  if (isNew) {
    Object.keys(schema.properties).forEach(propertyKey => {
      if (schema.properties[propertyKey].default) {
        initialFormData[propertyKey] = schema.properties[propertyKey].default;
      }
    });
  }

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="StUF-ZDS registration options modal title"
          defaultMessage="Plugin configuration: StUF-ZDS"
        />
      }
      initialFormData={normalizeFormData(initialFormData)}
      onSubmit={values => onChange({formData: values})}
    >
      <StufZDSOptionsFormFields name={name} schema={schema} />
    </ModalOptionsConfiguration>
  );
};

StufZDSOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']),
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  formData: PropTypes.shape({
    variablesMapping: PropTypes.arrayOf(
      PropTypes.shape({
        formVariable: PropTypes.string,
        stufName: PropTypes.string,
        serializeListToCsv: PropTypes.bool,
      })
    ),
    variablesMappingInitiator: PropTypes.arrayOf(
      PropTypes.shape({
        formVariable: PropTypes.string,
        stufName: PropTypes.string,
        serializeListToCsv: PropTypes.bool,
      })
    ),
    zdsDocumenttypeOmschrijvingInzending: PropTypes.string,
    zdsZaakdocVertrouwelijkheid: PropTypes.string,
    zdsZaaktypeCode: PropTypes.string,
    zdsZaaktypeOmschrijving: PropTypes.string,
    zdsZaaktypeStatusCode: PropTypes.string,
    zdsZaaktypeStatusOmschrijving: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default StufZDSOptionsForm;
