import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useMemo} from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {
  DocumentTypeSelect as GenericDocumentTypeSelect,
  useGetDocumentTypes,
} from 'components/admin/forms/zgw';

const DOCUMENT_TYPES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/document-types';

// Components

const DocumentTypeSelect = ({catalogueUrl = ''}) => {
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
      <Field
        name="documentTypeDescription"
        // TODO: make required once legacy config is dropped
        required={false}
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'document type' label"
            defaultMessage="Document type"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'document type' helpText"
            defaultMessage={`Documents produced in the form submission are registered
            with this document type, unless more fine grained configuration is available.
            Only document types available on the selected case type are shown.`}
          />
        }
        noManageChildProps
      >
        <GenericDocumentTypeSelect
          name="documentTypeDescription"
          documentTypes={documentTypes}
          isDisabled={!zgwApiGroup || !caseTypeIdentification}
          // TODO: make required once legacy config is dropped
          isRequired={false}
          isLoading={loading}
        />
      </Field>
    </FormRow>
  );
};

DocumentTypeSelect.propTypes = {
  catalogueUrl: PropTypes.string,
};

export default DocumentTypeSelect;
