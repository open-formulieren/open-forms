import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import {ValidationErrorContext, filterErrors} from 'components/admin/forms/ValidationErrors';
import {getChoicesFromSchema} from 'utils/json-schema';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';

const ObjectsApiOptionsForm = ({index, name, label, schema, formData, onChange}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const {objectsApiGroup} = schema.properties;
  const apiGroupChoices = getChoicesFromSchema(objectsApiGroup.enum, objectsApiGroup.enumNames);
  const numErrors = filterErrors(name, validationErrors).length;
  const defaultGroup = apiGroupChoices.length === 1 ? apiGroupChoices[0][0] : undefined;

  // default to version 2, existing form data can override this
  const version = formData?.version ?? 2;

  return (
    <ModalOptionsConfiguration
      name={name}
      label={label}
      numErrors={numErrors}
      modalTitle={
        <FormattedMessage
          description="Objects API registration options modal title"
          defaultMessage="Plugin configuration: Objects API"
        />
      }
      initialFormData={{
        version,
        // Only for version 2 we set the `variablesMapping`
        variablesMapping: version === 2 ? [] : undefined,
        ...formData,
        // Ensure that if there's only one option, it is automatically selected.
        objectsApiGroup: formData.objectsApiGroup ?? defaultGroup,
      }}
      onSubmit={values => onChange({formData: values})}
    >
      <ObjectsApiOptionsFormFields index={index} name={name} apiGroupChoices={apiGroupChoices} />
    </ModalOptionsConfiguration>
  );
};

ObjectsApiOptionsForm.propTypes = {
  index: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    properties: PropTypes.shape({
      objectsApiGroup: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.string).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }).isRequired,
  }).isRequired,
  formData: PropTypes.shape({
    version: PropTypes.number,
    objectsApiGroup: PropTypes.string,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.number,
    updateExistingObject: PropTypes.bool,
    authAttributePath: PropTypes.arrayOf(PropTypes.string),
    productaanvraagType: PropTypes.string,
    informatieobjecttypeSubmissionReport: PropTypes.string,
    uploadSubmissionCsv: PropTypes.bool,
    informatieobjecttypeSubmissionCsv: PropTypes.string,
    informatieobjecttypeAttachment: PropTypes.string,
    organisatieRsin: PropTypes.string,
    contentJson: PropTypes.string,
    paymentStatusUpdateJson: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default ObjectsApiOptionsForm;
