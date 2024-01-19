import PropTypes from 'prop-types';
import React from 'react';

import Field from 'components/admin/forms/Field';

import ZGWFormFields from './ZGWOptionsFormFields';

const ZGWOptionsForm = ({index, name, label, schema, formData, onChange}) => {
  return (
    <Field name={name} label={label}>
      <ZGWFormFields
        index={index}
        name={name}
        schema={schema}
        formData={formData}
        onChange={formData => onChange({formData})}
      />
    </Field>
  );
};

ZGWOptionsForm.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
  label: PropTypes.node,
  schema: PropTypes.shape({
    contentJson: PropTypes.string,
    informatieobjecttype: PropTypes.string,
    medewerkerRoltype: PropTypes.string,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.number,
    organisatieRsin: PropTypes.string,
    variablesProperties: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenshap: PropTypes.string,
      })
    ),
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    zaaktype: PropTypes.string,
    zgwApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  formData: PropTypes.shape({
    contentJson: PropTypes.string,
    informatieobjecttype: PropTypes.string,
    medewerkerRoltype: PropTypes.string,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    organisatieRsin: PropTypes.string,
    variablesProperties: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenshap: PropTypes.string,
      })
    ).isRequired,
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    zaaktype: PropTypes.string,
    zgwApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  onChange: PropTypes.func.isRequired,
};

export default ZGWOptionsForm;
