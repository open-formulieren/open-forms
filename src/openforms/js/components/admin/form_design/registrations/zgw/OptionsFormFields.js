import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';

import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import {TextArea, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';

import {VariablePropertyModal} from './OptionsVariablesProperties';
import {getChoicesFromSchema, getErrorMarkup} from './utils';

const Wrapper = ({children}) => (
  <form className="rjsf" name="form.registrationBackendOptions">
    <CustomFieldTemplate displayLabel={false} errors={null}>
      <fieldset id="root">{children}</fieldset>
    </CustomFieldTemplate>
  </form>
);

const ZGWFormFields = ({index, name, schema, formData, onChange}) => {
  const intl = useIntl();
  const validationErrors = useContext(ValidationErrorContext);

  const {
    zgwApiGroup = '',
    zaakVertrouwelijkheidaanduiding = '',
    zaaktype = '',
    informatieobjecttype = '',
    organisatieRsin = '',
    medewerkerRoltype = '',
    objecttype = '',
    objecttypeVersion = '',
    contentJson = '',
  } = formData;

  const onFieldChange = event => {
    const {name, value} = event.target;
    const updatedFormData = produce(formData, draft => {
      draft[name] = value;
    });
    onChange(updatedFormData);
  };

  const getFieldErrors = (index, errors, field) => {
    const errorMessages = [];

    for (const [errorName, errorReason] of errors) {
      if (errorName.startsWith(name)) {
        const errorNameBits = errorName.split('.');
        if (
          errorNameBits[2] === String(index) &&
          errorNameBits[errorNameBits.length - 1] === field
        ) {
          errorMessages.push(errorReason);
        }
      }
    }

    return errorMessages.length > 0 ? errorMessages : null;
  };

  return (
    <Wrapper>
      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'ZGW API set',
          description: 'ZGW API set',
        })}
        rawDescription={intl.formatMessage({
          description: 'ZGW API set selection',
          defaultMessage: 'Which ZGW API set to use.',
        })}
        rawErrors={null}
        errors={null}
        displayLabel
      >
        <Select
          id="zgwApiGroup"
          name="zgwApiGroup"
          choices={getChoicesFromSchema(
            schema?.properties?.zgwApiGroup?.enum,
            schema?.properties?.zgwApiGroup?.enumNames
          )}
          value={zgwApiGroup}
          onChange={onFieldChange}
          allowBlank
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Zaaktype',
          description: 'URL of the ZAAKTYPE in the Catalogi API',
        })}
        rawDescription={intl.formatMessage({
          description: 'ZAAKTYPE URL',
          defaultMessage: 'URL of the ZAAKTYPE in the Catalogi API.',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'zaaktype')}
        errors={
          getFieldErrors(index, validationErrors, 'zaaktype')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'zaaktype'))
            : null
        }
        displayLabel
      >
        <TextInput id="root_zaaktype" name="zaaktype" value={zaaktype} onChange={onFieldChange} />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Informatieobjecttype',
          description: 'URL of the INFORMATIEOBJECTTYPE in the Catalogi API',
        })}
        rawDescription={intl.formatMessage({
          description: 'Informatieobjecttype URL',
          defaultMessage: 'URL of the INFORMATIEOBJECTTYPE in the Catalogi API.',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'informatieobjecttype')}
        errors={
          getFieldErrors(index, validationErrors, 'informatieobjecttype')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'informatieobjecttype'))
            : null
        }
        displayLabel
      >
        <TextInput
          id="root_informatieobjecttype"
          name="informatieobjecttype"
          value={informatieobjecttype}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Organisatie rsin',
          description: 'RSIN of organization, which creates the ZAAK',
        })}
        rawDescription={intl.formatMessage({
          description: 'Organisatie rsin',
          defaultMessage: 'RSIN of organization, which creates the ZAAK.',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'organisatieRsin')}
        errors={
          getFieldErrors(index, validationErrors, 'organisatieRsin')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'organisatieRsin'))
            : null
        }
        displayLabel
      >
        <TextInput
          id="root_organisatieRsin"
          name="organisatieRsin"
          value={organisatieRsin}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Confidentiality',
          description:
            'Indication of the level to which extend the dossier of the ZAAK is meant to be public',
        })}
        rawDescription={intl.formatMessage({
          description: 'Confidentiality',
          defaultMessage:
            'Indication of the level to which extend the dossier of the ZAAK is meant to be public.',
        })}
        rawErrors={null}
        errors={null}
        displayLabel
      >
        <Select
          id="root_zaakVertrouwelijkheidaanduiding"
          name="zaakVertrouwelijkheidaanduiding"
          choices={getChoicesFromSchema(
            schema?.properties?.zaakVertrouwelijkheidaanduiding?.enum,
            schema?.properties?.zaakVertrouwelijkheidaanduiding?.enumNames
          )}
          value={zaakVertrouwelijkheidaanduiding}
          onChange={onFieldChange}
          allowBlank
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Medewerker roltype',
          description:
            'Description (omschrijving) of the ROLTYPE to use for employees filling in a form for a citizen/company',
        })}
        rawDescription={intl.formatMessage({
          description: 'Medewerker roltype',
          defaultMessage:
            'Description (omschrijving) of the ROLTYPE to use for employees filling in a form for a citizen/company.',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'medewerkerRoltype')}
        errors={
          getFieldErrors(index, validationErrors, 'medewerkerRoltype')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'medewerkerRoltype'))
            : null
        }
        displayLabel
      >
        <TextInput
          id="root_medewerkerRoltype"
          name="medewerkerRoltype"
          value={medewerkerRoltype}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Objects API - objecttype',
          description:
            'URL to the OBJECT TYPE for the "Product Request" in the Object Types API. The object type must contain the following attributes: 1) submission_id 2) type (the type of the "Product Request") 3) data (submitted form data)',
        })}
        rawDescription={intl.formatMessage({
          description: 'Objects API - objecttype',
          defaultMessage:
            'URL to the OBJECT TYPE for the "Product Request" in the Object Types API. The object type must contain the following attributes: 1) submission_id 2) type (the type of the "Product Request") 3) data (submitted form data).',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'objecttype')}
        errors={
          getFieldErrors(index, validationErrors, 'objecttype')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'objecttype'))
            : null
        }
        displayLabel
      >
        <TextInput
          id="root_objecttype"
          name="objecttype"
          value={objecttype}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Objects API - objecttype version',
          description: 'Version of the object type in the Object Types API',
        })}
        rawDescription={intl.formatMessage({
          description: 'Objects API - objecttype version',
          defaultMessage: 'Version of the object type in the Object Types API.',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'objecttypeVersion')}
        errors={
          getFieldErrors(index, validationErrors, 'objecttypeVersion')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'objecttypeVersion'))
            : null
        }
        displayLabel
      >
        <TextInput
          id="root_objecttypeVersion"
          name="objecttypeVersion"
          value={objecttypeVersion}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        label={intl.formatMessage({
          defaultMessage: 'Objects API - JSON content field',
          description: 'JSON template for the content of the request sent to the Objects API',
        })}
        rawDescription={intl.formatMessage({
          description: 'Objects API - JSON content field',
          defaultMessage: 'JSON template for the content of the request sent to the Objects API.',
        })}
        rawErrors={getFieldErrors(index, validationErrors, 'contentJson')}
        errors={
          getFieldErrors(index, validationErrors, 'contentJson')
            ? getErrorMarkup(getFieldErrors(index, validationErrors, 'contentJson'))
            : null
        }
        displayLabel
      >
        <TextArea
          id="root_contentJson"
          name="contentJson"
          value={contentJson}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <VariablePropertyModal formData={formData} onChange={onChange} />
    </Wrapper>
  );
};

ZGWFormFields.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
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
    zgwApiGroup: PropTypes.number,
  }),
  formData: PropTypes.shape({
    // matches the backend serializer
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
    zgwApiGroup: PropTypes.number,
  }),
  onChange: PropTypes.func.isRequired,
};

export default ZGWFormFields;
