import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';

import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import {TextArea, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';

import {VariablePropertyModal} from './ZGWOptionsVariablesProperties';
import {getChoicesFromSchema, getErrorMarkup, getFieldErrors} from './utils';

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

  const buildErrorsComponent = field => {
    const rawErrors = getFieldErrors(name, index, validationErrors, field);
    return rawErrors ? getErrorMarkup(rawErrors) : null;
  };

  return (
    <Wrapper>
      <CustomFieldTemplate
        id="root_zgwApiGroup"
        label={intl.formatMessage({
          defaultMessage: 'ZGW API group',
          description: 'ZGW API group',
        })}
        rawDescription={intl.formatMessage({
          description: 'ZGW API group selection',
          defaultMessage: 'Which ZGW API group to use.',
        })}
        rawErrors={null}
        errors={null}
        displayLabel
      >
        <Select
          id="root_zgwApiGroup"
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
        id="root_zaaktype"
        label={intl.formatMessage({
          defaultMessage: 'Zaaktype',
          description: 'URL of the ZAAKTYPE in the Catalogi API',
        })}
        rawDescription={intl.formatMessage({
          description: 'ZAAKTYPE URL',
          defaultMessage: 'URL of the ZAAKTYPE in the Catalogi API.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'zaaktype')}
        errors={buildErrorsComponent('zaaktype')}
        displayLabel
      >
        <TextInput id="root_zaaktype" name="zaaktype" value={zaaktype} onChange={onFieldChange} />
      </CustomFieldTemplate>

      <CustomFieldTemplate
        id="root_informatieobjecttype"
        label={intl.formatMessage({
          defaultMessage: 'Informatieobjecttype',
          description: 'URL of the INFORMATIEOBJECTTYPE in the Catalogi API',
        })}
        rawDescription={intl.formatMessage({
          description: 'Informatieobjecttype URL',
          defaultMessage: 'URL of the INFORMATIEOBJECTTYPE in the Catalogi API.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'informatieobjecttype')}
        errors={buildErrorsComponent('informatieobjecttype')}
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
        id="root_organisatieRsin"
        label={intl.formatMessage({
          defaultMessage: 'Organisatie rsin',
          description: 'RSIN of organization, which creates the ZAAK',
        })}
        rawDescription={intl.formatMessage({
          description: 'Organisatie rsin',
          defaultMessage: 'RSIN of organization, which creates the ZAAK.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'organisatieRsin')}
        errors={buildErrorsComponent('organisatieRsin')}
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
        id="root_zaakVertrouwelijkheidaanduiding"
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
        id="root_medewerkerRoltype"
        label={intl.formatMessage({
          defaultMessage: 'Medewerker roltype',
          description:
            'Description (omschrijving) of the ROLTYPE to use for employees filling in a form for a citizen/company',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'Medewerker roltype',
          description:
            'Description (omschrijving) of the ROLTYPE to use for employees filling in a form for a citizen/company.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'medewerkerRoltype')}
        errors={buildErrorsComponent('medewerkerRoltype')}
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
        id="root_objecttype"
        label={intl.formatMessage({
          defaultMessage: 'Objects API - objecttype',
          description:
            'URL to the OBJECT TYPE for the "Product Request" in the Object Types API. The object type must contain the following attributes: 1) submission_id 2) type (the type of the "Product Request") 3) data (submitted form data)',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'Objects API - objecttype',
          description:
            'URL to the OBJECT TYPE for the "Product Request" in the Object Types API. The object type must contain the following attributes: 1) submission_id 2) type (the type of the "Product Request") 3) data (submitted form data).',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'objecttype')}
        errors={buildErrorsComponent('objecttype')}
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
        id="root_objecttypeVersion"
        label={intl.formatMessage({
          defaultMessage: 'Objects API - objecttype version',
          description: 'Version of the object type in the Object Types API',
        })}
        rawDescription={intl.formatMessage({
          description: 'Objects API - objecttype version',
          defaultMessage: 'Version of the object type in the Object Types API.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'objecttypeVersion')}
        errors={buildErrorsComponent('objecttypeVersion')}
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
        id="root_contentJson"
        label={intl.formatMessage({
          defaultMessage: 'Objects API - JSON content field',
          description: 'JSON template for the content of the request sent to the Objects API',
        })}
        rawDescription={intl.formatMessage({
          description: 'Objects API - JSON content field',
          defaultMessage: 'JSON template for the content of the request sent to the Objects API.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'contentJson')}
        errors={buildErrorsComponent('contentJson')}
        displayLabel
      >
        <TextArea
          id="root_contentJson"
          name="contentJson"
          value={contentJson}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>

      <VariablePropertyModal index={index} name={name} formData={formData} onChange={onChange} />
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
    propertyMappings: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenschap: PropTypes.string,
      })
    ),
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    zaaktype: PropTypes.string,
    zgwApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  formData: PropTypes.shape({
    // matches the backend serializer
    contentJson: PropTypes.string,
    informatieobjecttype: PropTypes.string,
    medewerkerRoltype: PropTypes.string,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    organisatieRsin: PropTypes.string,
    propertyMappings: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenschap: PropTypes.string,
      })
    ),
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    zaaktype: PropTypes.string,
    zgwApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  onChange: PropTypes.func.isRequired,
};

export default ZGWFormFields;
