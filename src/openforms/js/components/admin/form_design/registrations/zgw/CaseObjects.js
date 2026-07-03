import {FieldArray, useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextArea, TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {DeleteIcon} from 'components/admin/icons';

const OverigeFields = ({index}) => {
  const name = `caseObjects.${index}.caseObjectIdentification.overigeData`;
  const [fieldProps] = useField(name);
  return (
    <FormRow>
      <Field
        name={name}
        required
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'overigeData' label"
            defaultMessage="Overige data"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'overigeData' help text"
            defaultMessage={`Data for the 'overige' case object in a free format. You can use form variables here.`}
          />
        }
      >
        <TextArea id={`id_${name}`} rows={2} cols={85} required {...fieldProps} />
      </Field>
    </FormRow>
  );
};

OverigeFields.propTypes = {
  index: PropTypes.number.isRequired,
};

// mapping of caseObjectType and related objectIdentification fields
// now we support only 'overige' type
export const CASE_OBJECT_TYPES_FIELDS = {
  overige: OverigeFields,
};

const CaseObjectType = ({index, options}) => {
  const name = `caseObjects.${index}.caseObjectType`;
  return (
    <FormRow>
      <Field
        name={name}
        required
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'caseObjectType' label"
            defaultMessage="Object type"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'caseObjectType' help text"
            defaultMessage={`Type of the case object. Now only 'overige' value is supported.`}
          />
        }
      >
        <ReactSelect
          name={name}
          required
          options={options.map(([value, label]) => ({
            value,
            label,
          }))}
          isClearable
        />
      </Field>
    </FormRow>
  );
};

CaseObjectType.propTypes = {
  index: PropTypes.number.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
};

const CaseObjectTypeOverige = ({index}) => {
  const name = `caseObjects.${index}.caseObjectTypeOverige`;
  const [fieldProps] = useField(name);
  return (
    <FormRow>
      <Field
        name={name}
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'caseObjectTypeOverige' label"
            defaultMessage="Object type overige"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'caseObjectTypeOverige' help text"
            defaultMessage={`Description of the 'overige' object type.`}
          />
        }
      >
        <TextInput id={`id_${name}`} {...fieldProps} />
      </Field>
    </FormRow>
  );
};

CaseObjectTypeOverige.propTypes = {
  index: PropTypes.number.isRequired,
};

const CaseObjectFieldset = ({index, caseObjectTypeChoices, onDelete}) => {
  const prefix = `caseObjects.${index}`;
  const [{value: caseObjectTypeValue}] = useField(`${prefix}.caseObjectType`);
  const ObjectIdentificationFields = CASE_OBJECT_TYPES_FIELDS[caseObjectTypeValue];

  const formik = useFormikContext();
  console.log('Formik values:', formik.values);

  return (
    <Fieldset
      title={
        <>
          <FormattedMessage
            description="ZGW APIs registration: case objects fieldset title"
            defaultMessage="Case object {count}"
            values={{
              count: index + 1,
            }}
          />
          <DeleteIcon onConfirm={onDelete} />
        </>
      }
      fieldNames={[
        `${prefix}.caseObjectType`,
        `${prefix}.caseObjectTypeOverige`,
        `${prefix}.caseObjectIdentification`,
      ]}
    >
      <CaseObjectType index={index} options={caseObjectTypeChoices} />
      <CaseObjectTypeOverige index={index} />

      {ObjectIdentificationFields ? <ObjectIdentificationFields index={index} /> : null}
    </Fieldset>
  );
};

CaseObjectFieldset.propTypes = {
  index: PropTypes.number.isRequired,
  caseObjectTypeChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
  onDelete: PropTypes.func.isRequired,
};

const CaseObjectFieldsets = ({caseObjectTypeChoices}) => {
  const {
    values: {caseObjects = []},
  } = useFormikContext();

  return (
    <FieldArray name="caseObjects">
      {arrayHelpers => (
        <>
          {caseObjects.map((value, index) => (
            <CaseObjectFieldset
              key={index}
              index={index}
              caseObjectTypeChoices={caseObjectTypeChoices}
              onDelete={() => arrayHelpers.remove(index)}
            />
          ))}
          <ButtonContainer
            onClick={() =>
              arrayHelpers.push({
                caseObjectType: '',
                caseObjectTypeOverige: '',
                caseObjectIdentification: {
                  overigeData: '',
                },
              })
            }
          >
            <FormattedMessage
              description="Add case object (mapping) button"
              defaultMessage="Add case object"
            />
          </ButtonContainer>
        </>
      )}
    </FieldArray>
  );
};

CaseObjectFieldsets.propTypes = {
  caseObjectTypeChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
};

export default CaseObjectFieldsets;
