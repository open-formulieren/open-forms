import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useEffect} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, usePrevious} from 'react-use';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

import CatalogueSelect, {extractValue as getCatalogueOption} from './CatalogueSelect';

// Data fetching

const CATALOGUES_ENDPOINT = '/api/v2/registration/plugins/objects-api/catalogues';
const IOT_ENDPOINT = '/api/v2/registration/plugins/objects-api/informatieobjecttypen';

const getCatalogues = async apiGroupID => {
  const response = await get(CATALOGUES_ENDPOINT, {objects_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available catalogues failed');
  }
  const catalogues = response.data;

  const _optionsByRSIN = {};
  for (const catalogue of catalogues) {
    const {rsin} = catalogue;
    if (!_optionsByRSIN[rsin]) _optionsByRSIN[rsin] = [];
    _optionsByRSIN[rsin].push(catalogue);
  }

  const groups = Object.entries(_optionsByRSIN)
    .map(([rsin, options]) => ({
      label: rsin,
      options: options.sort((a, b) => a.label.localeCompare(b.label)),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return groups;
};

const getDocumentTypes = async (apiGroupID, catalogueUrl) => {
  const response = await get(IOT_ENDPOINT, {
    objects_api_group: apiGroupID,
    catalogus_url: catalogueUrl,
  });
  if (!response.ok) {
    throw new Error('Loading available document types failed');
  }
  const documentTypes = response.data.sort((a, b) => a.omschrijving.localeCompare(b.omschrijving));
  return documentTypes.map(({omschrijving}) => ({
    value: omschrijving,
    label: omschrijving,
  }));
};

// Components

const DocumentType = ({name, label, loading, options, isDisabled, helpText}) => {
  const [, , fieldHelpers] = useField(name);
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <Field name={name} label={label} helpText={helpText} noManageChildProps>
        <ReactSelect
          name={name}
          options={options}
          isLoading={loading}
          isDisabled={isDisabled}
          onChange={selectedOption => {
            // unset form key entirely if the selection is cleared
            setValue(selectedOption ? selectedOption.value : undefined);
          }}
          isClearable
        />
      </Field>
    </FormRow>
  );
};

DocumentType.propTypes = {
  name: PropTypes.oneOf(['iotSubmissionReport', 'iotSubmissionCsv', 'iotAttachment']).isRequired,
  label: PropTypes.node.isRequired,
  loading: PropTypes.bool.isRequired,
  isDisabled: PropTypes.bool.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    })
  ).isRequired,
  helpText: PropTypes.node,
};

export const DocumentTypesFieldet = () => {
  const {values, setValues} = useFormikContext();
  const {objectsApiGroup = null, catalogue = undefined} = values;

  // fetch available catalogues and re-use the result
  const {
    loading: loadingCatalogues,
    value: catalogueOptionGroups = [],
    error: cataloguesError,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    return await getCatalogues(objectsApiGroup);
  }, [objectsApiGroup]);
  if (cataloguesError) throw cataloguesError;

  const catalogueValue = getCatalogueOption(catalogueOptionGroups, catalogue || {});
  const catalogueUrl = catalogueValue?.url;
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

  const {
    loading,
    value: documentTypeOptions = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    if (!catalogueUrl) return [];
    return await getDocumentTypes(objectsApiGroup, catalogueUrl);
  }, [objectsApiGroup, catalogueUrl]);
  if (error) throw error;

  const documentTypeProps = {
    isDisabled: !objectsApiGroup || !catalogueUrl,
    loading: loading,
    options: documentTypeOptions,
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
      <CatalogueSelect loading={loadingCatalogues} optionGroups={catalogueOptionGroups} />
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
    </Fieldset>
  );
};
