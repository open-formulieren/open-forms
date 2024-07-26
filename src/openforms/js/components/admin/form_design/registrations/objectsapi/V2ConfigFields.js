import {produce} from 'immer';
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

const V2ConfigFields = ({index, name, schema, formData, onFieldChange, onChange}) => {
  const intl = useIntl();
  const validationErrors = useContext(ValidationErrorContext);

  const {
    objectsApiGroup = '',
    objecttype = '',
    objecttypeVersion = '',
    informatieobjecttypeSubmissionReport = '',
    updateExistingObject = false,
    uploadSubmissionCsv = false,
    informatieobjecttypeSubmissionCsv = '',
    informatieobjecttypeAttachment = '',
    organisatieRsin = '',
    variablesMapping = [],
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
      onFieldChange({
        target: {name: 'objectsApiGroup', value: schema.properties.objectsApiGroup.enum[0]},
      });
    }
  }, []);

  const clearMappingOnChange = message => {
    return event => {
      if (variablesMapping.length === 0) {
        onFieldChange(event);
      } else {
        const confirmSwitch = window.confirm(message);
        if (confirmSwitch) {
          const {name, value} = event.target;
          onChange(
            produce(formData, draft => {
              draft.variablesMapping = [];
              draft[name] = value;
            })
          );
        }
      }
    };
  };

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
          onChange={clearMappingOnChange(
            intl.formatMessage({
              defaultMessage: `Changing the Objects API group will remove the existing variables mapping.
            Are you sure you want to continue?`,
              description: 'Changing Objects API group warning message',
            })
          )}
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
            'UUID of the ProductAanvraag objecttype in the Objecttypes API. The objecttype should have the following three attributes: "submission_id", "type" (the type of productaanvraag) and "data" (the submitted form data)',
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
          onChange={clearMappingOnChange(
            intl.formatMessage({
              defaultMessage: `Changing the objecttype will remove the existing variables mapping.
            Are you sure you want to continue?`,
              description: 'Changing objecttype warning message',
            })
          )}
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
          onChange={onFieldChange}
        />
      </CustomFieldTemplate>
      <CustomFieldTemplate
        id="root_updateExistingObject"
        label={intl.formatMessage({
          defaultMessage: 'Update existing object',
          description: 'Objects API registration options "Update existing object" label',
        })}
        rawDescription={intl.formatMessage({
          defaultMessage:
            'Indicates whether the existing object (retrieved from an optional initial data reference) should be updated, instead of creating a new one. If no existing object exists, a new one will be created instead',
          description: 'Objects API registration options "Update existing object" description',
        })}
        rawErrors={getFieldErrors(name, index, validationErrors, 'updateExistingObject')}
        errors={buildErrorsComponent('updateExistingObject')}
        displayLabel
      >
        <Checkbox
          id="root_updateExistingObject"
          name="updateExistingObject"
          checked={updateExistingObject}
          onChange={e =>
            onFieldChange({target: {name: 'updateExistingObject', value: !updateExistingObject}})
          }
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
    updateExistingObject: PropTypes.bool,
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

export default V2ConfigFields;
