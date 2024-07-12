import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useContext, useEffect} from 'react';
import {useIntl} from 'react-intl';
import {useUpdateEffect} from 'react-use';

import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import {Checkbox, NumberInput, TextArea, TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';

import CatalogiSelect from '../CatalogiSelect';
import InformatieObjecttypeSelect from '../InformatieObjecttypeSelect';
import {useGetAvailableCatalogi, useGetAvailableInformatieObjecttypen} from './hooks';
import {getErrorMarkup, getFieldErrors, getOptionsFromSchema} from './utils';

const LegacyConfigFields = ({index, name, schema, formData, onFieldChange, onChange}) => {
  const intl = useIntl();
  const validationErrors = useContext(ValidationErrorContext);

  const {
    objectsApiGroup = '',
    objecttype = '',
    objecttypeVersion = '',
    catalogusDomein = '',
    catalogusRsin = '',
    productaanvraagType = '',
    informatieobjecttypeSubmissionReport = '',
    uploadSubmissionCsv = false,
    informatieobjecttypeSubmissionCsv = '',
    informatieobjecttypeAttachment = '',
    organisatieRsin = '',
    contentJson = '',
    paymentStatusUpdateJson = '',
  } = formData;

  const availableCatalogiState = useGetAvailableCatalogi(objectsApiGroup);
  const availableInformatieObjecttypenState = useGetAvailableInformatieObjecttypen(
    objectsApiGroup,
    catalogusDomein,
    catalogusRsin
  );

  const buildErrorsComponent = field => {
    const rawErrors = getFieldErrors(name, index, validationErrors, field);
    return rawErrors ? getErrorMarkup(rawErrors) : null;
  };

  useEffect(() => {
    if (schema.properties.objectsApiGroup.enum.length === 1 && objectsApiGroup === '') {
      onFieldChange({
        target: {name: 'objectsApiGroup', value: schema.properties.objectsApiGroup.enum[0]},
      });
    }
  }, []);

  // Resetting values if necessary:
  useUpdateEffect(() => {
    onChange(
      produce(formData, draft => {
        delete draft.objecttype;
        delete draft.objecttypeVersion;
        delete draft.catalogusDomein;
        delete draft.catalogusRsin;
        delete draft.informatieobjecttypeSubmissionReport;
        delete draft.informatieobjecttypeSubmissionCsv;
        delete draft.informatieobjecttypeAttachment;
      })
    );
  }, [objectsApiGroup]);

  useUpdateEffect(() => {
    onChange(
      produce(formData, draft => {
        draft.objecttypeVersion = '';
      })
    );
  }, [objecttype]);

  useUpdateEffect(() => {
    onChange(
      produce(formData, draft => {
        delete draft.informatieobjecttypeSubmissionReport;
        delete draft.informatieobjecttypeSubmissionCsv;
        delete draft.informatieobjecttypeAttachment;
      })
    );
  }, [catalogusDomein, catalogusRsin]);

  return (
    <>
      <CustomFieldTemplate
        id="root_objectsApiGroup"
        label={intl.formatMessage({
          defaultMessage: 'Objects API group',
          description: 'Objects API group',
        })}
        rawDescription={intl.formatMessage({
          description: 'Objects API group selection',
          defaultMessage: 'Which Objects API group to use.',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'objectsApiGroup')}
        errors={buildErrorsComponent('objectsApiGroup')}
        displayLabel
        required
      >
        <ReactSelect
          name="objectsApiGroup"
          value={objectsApiGroup}
          options={getOptionsFromSchema(
            schema.properties.objectsApiGroup.enum,
            schema.properties.objectsApiGroup.enumNames
          )}
          htmlId="root_objectsApiGroup"
          onChange={onFieldChange}
          emptyValue=""
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_objecttype"
        label={intl.formatMessage({
          defaultMessage: 'Objecttype',
          description: 'Objects API registration options "Objecttype" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'UUID of the ProductAanvraag objecttype in the Objecttypes API. The objecttype should have the following three attributes: "submission_id", "type" (the type of productaanvraag) and "data" (the submitted form data)',
          description: 'Objects API registration options "Objecttype" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'objecttype')}
        errors={buildErrorsComponent('objecttype')}
        displayLabel
        required
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
          defaultMessage: 'Objecttype version',
          description: 'Objects API registration options "Objecttype version" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'Version of the objecttype in the Objecttypes API',
          description: 'Objects API registration options "Objecttype version" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'objecttypeVersion')}
        errors={buildErrorsComponent('objecttypeVersion')}
        displayLabel
        required
      >
        <NumberInput
          id="root_objecttypeVersion"
          name="objecttypeVersion"
          value={objecttypeVersion}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_catalogus"
        label={intl.formatMessage({
          defaultMessage: 'Catalog',
          description: 'Objects API registration options "Catalog" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'Which Catalog to use.',
          description: 'Objects API registration options "Catalog" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, [
          'catalogusDomein',
          'catalogusRsin',
        ])}
        errors={buildErrorsComponent(['catalogusDomein', 'catalogusRsin'])}
        displayLabel
        required
      >
        <CatalogiSelect
          name="catalogus"
          htmlId="root_catalogus"
          availableCatalogiState={availableCatalogiState}
          catalogusDomein={catalogusDomein}
          catalogusRsin={catalogusRsin}
          onChange={({catalogusDomein, catalogusRsin}) => {
            onChange(
              produce(formData, draft => {
                if (catalogusDomein === '' && catalogusRsin === '') {
                  delete draft.catalogusDomein;
                  delete draft.catalogusRsin;
                } else {
                  draft.catalogusDomein = catalogusDomein;
                  draft.catalogusRsin = catalogusRsin;
                }
              })
            );
          }}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_productaanvraagType"
        label={intl.formatMessage({
          defaultMessage: 'Productaanvraag type',
          description: 'Objects API registration options "Productaanvraag type" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'The type of ProductAanvraag',
          description: 'Objects API registration options "Productaanvraag type" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'productaanvraagType')}
        errors={buildErrorsComponent('productaanvraagType')}
        displayLabel
      >
        <TextInput
          id="root_productaanvraagType"
          name="productaanvraagType"
          value={productaanvraagType}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_informatieobjecttypeSubmissionReport"
        label={intl.formatMessage({
          defaultMessage: 'Submission report PDF informatieobjecttype',
          description:
            'Objects API registration options "Submission report PDF informatieobjecttype" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'Omschrijving of the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission report PDF',
          description:
            'Objects API registration options "Submission report PDF informatieobjecttype" description',
        })}
        rawErrors={getFieldErrors(
          name,
          index,
          validationErrors,
          'informatieobjecttypeSubmissionReport'
        )}
        errors={buildErrorsComponent('informatieobjecttypeSubmissionReport')}
        displayLabel
      >
        <InformatieObjecttypeSelect
          name="informatieobjecttypeSubmissionReport"
          htmlId="root_informatieobjecttypeSubmissionReport"
          availableInformatieObjecttypenState={availableInformatieObjecttypenState}
          informatieObjecttype={informatieobjecttypeSubmissionReport}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_uploadSubmissionCsv"
        label={intl.formatMessage({
          defaultMessage: 'Upload submission CSV',
          description: 'Objects API registration options "Upload submission CSV" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'Indicates whether or not the submission CSV should be uploaded as a Document in Documenten API and attached to the ProductAanvraag',
          description: 'Objects API registration options "Upload submission CSV" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'uploadSubmissionCsv')}
        errors={buildErrorsComponent('uploadSubmissionCsv')}
        displayLabel
      >
        <Checkbox
          id="root_uploadSubmissionCsv"
          name="uploadSubmissionCsv"
          checked={uploadSubmissionCsv}
          onChange={e =>
            onFieldChange({target: {name: 'uploadSubmissionCsv', value: !uploadSubmissionCsv}})
          }
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_informatieobjecttypeSubmissionCsv"
        label={intl.formatMessage({
          defaultMessage: 'Submission report CSV informatieobjecttype',
          description:
            'Objects API registration options "Submission report CSV informatieobjecttype" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'Omschrijving of the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission report CSV',
          description:
            'Objects API registration options "Submission report CSV informatieobjecttype" description',
        })}
        rawErrors={getFieldErrors(
          name,
          index,
          validationErrors,
          'informatieobjecttypeSubmissionCsv'
        )}
        errors={buildErrorsComponent('informatieobjecttypeSubmissionCsv')}
        displayLabel
      >
        <InformatieObjecttypeSelect
          name="informatieobjecttypeSubmissionCsv"
          htmlId="root_informatieobjecttypeSubmissionCsv"
          availableInformatieObjecttypenState={availableInformatieObjecttypenState}
          informatieObjecttype={informatieobjecttypeSubmissionCsv}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_informatieobjecttypeAttachment"
        label={intl.formatMessage({
          defaultMessage: 'Attachment informatieobjecttype',
          description: 'Objects API registration options "Attachment informatieobjecttype" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'Omschrijving of the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission attachments',
          description:
            'Objects API registration options "Attachment informatieobjecttype" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'informatieobjecttypeAttachment')}
        errors={buildErrorsComponent('informatieobjecttypeAttachment')}
        displayLabel
      >
        <InformatieObjecttypeSelect
          name="informatieobjecttypeAttachment"
          htmlId="root_informatieobjecttypeAttachment"
          availableInformatieObjecttypenState={availableInformatieObjecttypenState}
          informatieObjecttype={informatieobjecttypeAttachment}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_organisatieRsin"
        label={intl.formatMessage({
          defaultMessage: 'Organisation RSIN',
          description: 'Objects API registration options "Organisation RSIN" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'RSIN of organization, which creates the INFORMATIEOBJECT',
          description: 'Objects API registration options "Organisation RSIN" description',
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
        id="root_contentJson"
        label={intl.formatMessage({
          defaultMessage: 'JSON content field',
          description: 'Objects API registration options "JSON content field" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage: 'JSON template for the body of the request sent to the Objects API.',
          description: 'Objects API registration options "JSON content field" description',
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
      <CustomFieldTemplate
        id="root_paymentStatusUpdateJson"
        label={intl.formatMessage({
          defaultMessage: 'Payment status update JSON template',
          description:
            'Objects API registration options "Payment status update JSON template" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'This template is evaluated with the submission data and the resulting JSON is sent to the objects API with a PATCH to update the payment field.',
          description:
            'Objects API registration options "Payment status update JSON template" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'paymentStatusUpdateJson')}
        errors={buildErrorsComponent('paymentStatusUpdateJson')}
        displayLabel
      >
        <TextArea
          id="root_paymentStatusUpdateJson"
          name="paymentStatusUpdateJson"
          value={paymentStatusUpdateJson}
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
    </>
  );
};

LegacyConfigFields.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
  schema: PropTypes.any,
  formData: PropTypes.shape({
    objectsApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    version: PropTypes.number,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    productaanvraagType: PropTypes.string,
    informatieobjecttypeSubmissionReport: PropTypes.string,
    uploadSubmissionCsv: PropTypes.bool,
    informatieobjecttypeSubmissionCsv: PropTypes.string,
    informatieobjecttypeAttachment: PropTypes.string,
    organisatieRsin: PropTypes.string,
    contentJson: PropTypes.string,
    paymentStatusUpdateJson: PropTypes.string,
  }),
  onFieldChange: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default LegacyConfigFields;
