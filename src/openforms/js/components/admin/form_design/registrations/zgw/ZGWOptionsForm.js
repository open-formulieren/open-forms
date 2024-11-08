import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';
import {getChoicesFromSchema} from 'utils/json-schema';

import ZGWFormFields from './ZGWOptionsFormFields';

const ZGWOptionsForm = ({name, label, schema, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);

  const {zgwApiGroup, zaakVertrouwelijkheidaanduiding} = schema.properties;
  const apiGroupChoices = getChoicesFromSchema(zgwApiGroup.enum, zgwApiGroup.enumNames);
  const confidentialityLevelChoices = getChoicesFromSchema(
    zaakVertrouwelijkheidaanduiding.enum,
    zaakVertrouwelijkheidaanduiding.enumNames
  );

  const numErrors = filterErrors(name, validationErrors).length;
  const defaultGroup = apiGroupChoices.length === 1 ? apiGroupChoices[0][0] : undefined;

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="ZGW APIs registration options modal title"
          defaultMessage="Plugin configuration: ZGW APIs"
        />
      }
      initialFormData={{
        // defaults
        caseTypeIdentification: '',
        zaaktype: '',
        informatieobjecttype: '',
        organisatieRsin: '',
        zaakVertrouwelijkheidaanduiding: '',
        medewerkerRoltype: '',
        propertyMappings: [],
        // saved data, overwrites defaults
        ...formData,
        // Ensure that if there's only one option, it is automatically selected.
        zgwApiGroup: formData.zgwApiGroup ?? defaultGroup,
      }}
      onSubmit={values => onChange({formData: values})}
    >
      <ZGWFormFields
        name={name}
        apiGroupChoices={apiGroupChoices}
        confidentialityLevelChoices={confidentialityLevelChoices}
      />
    </ModalOptionsConfiguration>
  );
};

ZGWOptionsForm.propTypes = {
  name: PropTypes.string,
  label: PropTypes.node,
  schema: PropTypes.shape({
    properties: PropTypes.shape({
      zgwApiGroup: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.number).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
      zaakVertrouwelijkheidaanduiding: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.string).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }).isRequired,
  }).isRequired,
  formData: PropTypes.shape({
    zgwApiGroup: PropTypes.number,
    zaaktype: PropTypes.string,
    informatieobjecttype: PropTypes.string,
    organisatieRsin: PropTypes.string,
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    medewerkerRoltype: PropTypes.string,
    propertyMappings: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenschap: PropTypes.string,
      })
    ),
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    contentJson: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default ZGWOptionsForm;
