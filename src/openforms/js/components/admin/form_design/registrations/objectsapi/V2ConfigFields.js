import PropTypes from 'prop-types';
import React, {useContext, useEffect} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import ErrorMessage from 'components/errors/ErrorMessage';

import ObjectTypeSelect from './ObjectTypeSelect';
import ObjectTypeVersionSelect from './ObjectTypeVersionSelect';
import {useGetAvailableObjectTypes} from './hooks';
import {getChoicesFromSchema, getErrorMarkup, getFieldErrors} from './utils';

const V2ConfigFields = ({index, name, schema, formData, onChange}) => {
  const intl = useIntl();
  const validationErrors = useContext(ValidationErrorContext);

  const {
    objectsApiGroup = '',
    objecttype = '',
    objecttypeVersion = '',
    informatieobjecttypeSubmissionReport = '',
    uploadSubmissionCsv = '',
    informatieobjecttypeSubmissionCsv = '',
    informatieobjecttypeAttachment = '',
    organisatieRsin = '',
  } = formData;

  // Track available object types and versions in this component so the state can be
  // shared.
  const availableObjectTypesState = useGetAvailableObjectTypes(objectsApiGroup);

  const buildErrorsComponent = field => {
    const rawErrors = getFieldErrors(name, index, validationErrors, field);
    return rawErrors ? getErrorMarkup(rawErrors) : null;
  };

  useEffect(() => {
    if (schema.properties.objectsApiGroup.enum.length === 1 && objectsApiGroup === '') {
      onChange({
        target: {name: 'objectsApiGroup', value: schema.properties.objectsApiGroup.enum[0]},
      });
    }
  }, []);

  const loadingError = !!availableObjectTypesState.error;
  if (loadingError) {
    return (
      <ErrorMessage>
        <FormattedMessage
          defaultMessage="Something went wrong when fectching the available Objecttypes and versions"
          description="Objects API registrations options API error"
        />
      </ErrorMessage>
    );
  }

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
        <Select
          id="root_objectsApiGroup"
          name="objectsApiGroup"
          choices={getChoicesFromSchema(
            schema.properties.objectsApiGroup.enum,
            schema.properties.objectsApiGroup.enumNames
          )}
          value={objectsApiGroup}
          onChange={onChange}
          allowBlank
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
            'URL that points to the ProductAanvraag objecttype in the Objecttypes API. The objecttype should have the following three attributes: "submission_id", "type" (the type of productaanvraag) and "data" (the submitted form data)',
          description: 'Objects API registration options "Objecttype" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'objecttype')}
        errors={buildErrorsComponent('objecttype')}
        displayLabel
        required
      >
        {/* TODO: fallback to legacy UI if there are loading errors */}
        <ObjectTypeSelect
          availableObjectTypesState={availableObjectTypesState}
          objecttype={objecttype}
          onChange={onChange}
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
        {/* TODO: fallback to legacy UI if there are loading errors */}
        <ObjectTypeVersionSelect
          objectsApiGroup={objectsApiGroup}
          availableObjecttypes={availableObjectTypesState.availableObjecttypes}
          selectedObjecttype={objecttype}
          selectedVersion={objecttypeVersion}
          onChange={onChange}
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
            'URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission report PDF',
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
        <TextInput
          id="root_informatieobjecttypeSubmissionReport"
          name="informatieobjecttypeSubmissionReport"
          value={informatieobjecttypeSubmissionReport}
          onChange={onChange}
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
          value={uploadSubmissionCsv}
          onChange={onChange}
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
            'URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission report CSV',
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
        <TextInput
          id="root_informatieobjecttypeSubmissionCsv"
          name="informatieobjecttypeSubmissionCsv"
          value={informatieobjecttypeSubmissionCsv}
          onChange={onChange}
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
            'URL that points to the INFORMATIEOBJECTTYPE in the Catalogi API to be used for the submission attachments',
          description:
            'Objects API registration options "Attachment informatieobjecttype" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'informatieobjecttypeAttachment')}
        errors={buildErrorsComponent('informatieobjecttypeAttachment')}
        displayLabel
      >
        <TextInput
          id="root_informatieobjecttypeAttachment"
          name="informatieobjecttypeAttachment"
          value={informatieobjecttypeAttachment}
          onChange={onChange}
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
          onChange={onChange}
        />
      </CustomFieldTemplate>
    </>
  );
};

V2ConfigFields.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
  schema: PropTypes.any,
  formData: PropTypes.shape({
    objectsApiGroup: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    version: PropTypes.number,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    informatieobjecttypeSubmissionReport: PropTypes.string,
    uploadSubmissionCsv: PropTypes.string,
    informatieobjecttypeSubmissionCsv: PropTypes.string,
    informatieobjecttypeAttachment: PropTypes.string,
    organisatieRsin: PropTypes.string,
    contentJson: PropTypes.string,
    paymentStatusUpdateJson: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default V2ConfigFields;
