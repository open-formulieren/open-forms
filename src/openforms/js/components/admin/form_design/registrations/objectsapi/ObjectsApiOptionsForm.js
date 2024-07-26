import PropTypes from 'prop-types';
import React from 'react';

import Field from 'components/admin/forms/Field';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';

const ObjectsApiOptionsForm = ({index, name, label, schema, formData, onChange}) => {
  return (
    <Field name={name} label={label}>
      <ObjectsApiOptionsFormFields
        index={index}
        name={name}
        schema={schema}
        formData={formData}
        onChange={formData => onChange({formData})}
      />
    </Field>
  );
};

ObjectsApiOptionsForm.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
  label: PropTypes.node,
  schema: PropTypes.any,
  formData: PropTypes.shape({
    version: PropTypes.number,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    updateExistingObject: PropTypes.bool,
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
