import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext, useEffect, useMemo} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {usePrevious} from 'react-use';

import {FeatureFlagsContext} from 'components/admin/form_design/Context';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {
  CatalogueSelect,
  CopyDocumentTypesConfig,
  DocumentTypeSelect as GenericDocumentTypeSelect,
} from 'components/admin/forms/zgw';
import {WarningIcon} from 'components/admin/icons';

import {useGetDocumentTypes, useResolveCatalogue} from '../hooks';

export const DocumentType = ({name, label, loading, documentTypes, isDisabled, helpText}) => {
  const intl = useIntl();
  const [{value}] = useField(name);

  const {ZGW_APIS_INCLUDE_DRAFTS = false} = useContext(FeatureFlagsContext);

  const showWarning =
    !isDisabled &&
    value &&
    !loading &&
    documentTypes.find(option => option.value === value) === undefined;

  return (
    <FormRow>
      <Field name={name} label={label} helpText={helpText} disabled={isDisabled} noManageChildProps>
        <>
          <GenericDocumentTypeSelect
            name={name}
            documentTypes={documentTypes}
            isDisabled={isDisabled}
            isLoading={loading}
          />
          {showWarning && (
            <WarningIcon
              text={intl.formatMessage(
                {
                  description: 'Warning message about missing document type option.',
                  defaultMessage: `The value ''{value}' is set but could not be found. {draftsEnabled, select,
                      true {Possibly the draft was deleted.}
                      other {Perhaps this document type is not published yet?}
                    }`,
                },
                {value, draftsEnabled: ZGW_APIS_INCLUDE_DRAFTS}
              )}
            />
          )}
        </>
      </Field>
    </FormRow>
  );
};

DocumentType.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  loading: PropTypes.bool.isRequired,
  isDisabled: PropTypes.bool.isRequired,
  documentTypes: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
  helpText: PropTypes.node,
};

export const DocumentTypesFieldset = () => {
  const {values, setValues} = useFormikContext();
  const {objectsApiGroup = null, catalogue = undefined} = values;

  // fetch available catalogues and re-use the result
  const {
    loading: loadingCatalogues,
    catalogueOptionGroups,
    error: cataloguesError,
    catalogueUrl,
  } = useResolveCatalogue(objectsApiGroup, catalogue);
  if (cataloguesError) throw cataloguesError;
  const previousCatalogueUrl = usePrevious(catalogueUrl);

  // if the catalogue changes, reset the selected document types
  useEffect(() => {
    // only run the update if the catalogue is changed from one value to another
    // OR the catalogue was cleared.
    const hadCatalogueBefore = previousCatalogueUrl !== undefined;
    const hasCatalogueNow = catalogueUrl !== undefined;
    const isCleared = hadCatalogueBefore && !hasCatalogueNow;
    const hasChanged = hadCatalogueBefore && catalogueUrl !== previousCatalogueUrl;
    if (!isCleared && !hasChanged) return;

    setValues(prevValues => ({
      ...prevValues,
      iotSubmissionReport: undefined,
      iotSubmissionCsv: undefined,
      iotAttachment: undefined,
    }));
  }, [previousCatalogueUrl, catalogueUrl]);

  const {loading, documentTypes, error} = useGetDocumentTypes(objectsApiGroup, catalogueUrl);
  if (error) throw error;

  const documentTypeProps = {
    isDisabled: !objectsApiGroup || !catalogueUrl,
    loading: loading,
    documentTypes: documentTypes,
  };

  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Objects registration: document types"
          defaultMessage="Document types"
        />
      }
      collapsible
      fieldNames={['catalogue', 'iotSubmissionReport', 'iotSubmissionCsv', 'iotAttachment']}
    >
      <div className="description">
        <FormattedMessage
          description="New document types informative message"
          defaultMessage={`The legacy document types configuration will be ignored
        as soon as a catalogue is selected, even if you don't select any document
        type in the dropdowns.`}
        />
      </div>
      <CatalogueSelect
        label={
          <FormattedMessage
            description="Objects API registration options 'catalogue' label"
            defaultMessage="Catalogue"
          />
        }
        isDisabled={!objectsApiGroup}
        loading={loadingCatalogues}
        optionGroups={catalogueOptionGroups}
      />
      <DocumentType
        name="iotSubmissionReport"
        label={
          <FormattedMessage
            description='Objects API registration options "Submission report PDF informatieobjecttype" label'
            defaultMessage="Submission report PDF informatieobjecttype"
          />
        }
        {...documentTypeProps}
      />
      <DocumentType
        name="iotSubmissionCsv"
        label={
          <FormattedMessage
            description='Objects API registration options "Submission report CSV informatieobjecttype" label'
            defaultMessage="Submission report CSV informatieobjecttype"
          />
        }
        {...documentTypeProps}
      />
      <DocumentType
        name="iotAttachment"
        label={
          <FormattedMessage
            description='Objects API registration options "Attachment informatieobjecttype" label'
            defaultMessage="Attachment informatieobjecttype"
          />
        }
        {...documentTypeProps}
      />
      <CopyDocumentTypesConfig catalogueField="catalogue" descriptionField="iotAttachment" />
    </Fieldset>
  );
};
