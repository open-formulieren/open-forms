import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useMemo} from 'react';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {
  DocumentTypeSelect as GenericDocumentTypeSelect,
  useGetDocumentTypes,
} from 'components/admin/forms/zgw';

const DOCUMENT_TYPES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/document-types';

// Components

const DocumentTypeSelect = ({name, label, helpText, catalogueUrl = '', isRequired = false}) => {
  const {
    values: {zgwApiGroup = null, caseTypeIdentification = ''},
  } = useFormikContext();

  const query = useMemo(
    () => ({
      zgw_api_group: zgwApiGroup,
      catalogue_url: catalogueUrl,
      case_type_identification: caseTypeIdentification,
    }),
    [zgwApiGroup, catalogueUrl, caseTypeIdentification]
  );
  const {loading, documentTypes, error} = useGetDocumentTypes(DOCUMENT_TYPES_ENDPOINT, query);
  if (error) throw error;

  return (
    <FormRow>
      <Field name={name} required={isRequired} label={label} helpText={helpText} noManageChildProps>
        <GenericDocumentTypeSelect
          name={name}
          documentTypes={documentTypes}
          isDisabled={!zgwApiGroup || !caseTypeIdentification}
          isRequired={isRequired}
          isLoading={loading}
        />
      </Field>
    </FormRow>
  );
};

DocumentTypeSelect.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  helpText: PropTypes.node,
  catalogueUrl: PropTypes.string,
  isRequired: PropTypes.bool,
};

export default DocumentTypeSelect;
