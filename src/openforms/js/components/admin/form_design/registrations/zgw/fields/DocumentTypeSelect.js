import classNames from 'classnames';
import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

const DOCUMENT_TYPES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/document-types';

const getAvailableDocumentTypes = async (apiGroupID, catalogueUrl, caseTypeIdentification) => {
  const response = await get(DOCUMENT_TYPES_ENDPOINT, {
    zgw_api_group: apiGroupID,
    catalogue_url: catalogueUrl,
    case_type_identification: caseTypeIdentification,
  });
  if (!response.ok) {
    throw new Error('Loading available object types failed');
  }
  const documentTypes = response.data.sort((a, b) => a.description.localeCompare(b.description));
  return documentTypes.map(({description, isPublished}) => ({
    value: description,
    label: description,
    isPublished: isPublished,
  }));
};

// Components

const DocumentTypeSelectOption = props => {
  const {isPublished, label} = props.data;
  return (
    <components.Option {...props}>
      <span
        className={classNames('catalogi-type-option', {
          'catalogi-type-option--draft': !isPublished,
        })}
      >
        <FormattedMessage
          description="Document type option label"
          defaultMessage={`{label} {isPublished, select, false {<draft>(not published)</draft>} other {}}`}
          values={{
            label,
            isPublished,
            draft: chunks => <span className="catalogi-type-option__draft-suffix">{chunks}</span>,
          }}
        />
      </span>
    </components.Option>
  );
};

const DocumentTypeSelect = ({catalogueUrl = ''}) => {
  const [, , fieldHelpers] = useField('documentTypeDescription');
  const {
    values: {zgwApiGroup = null, caseTypeIdentification = ''},
  } = useFormikContext();
  const {setValue} = fieldHelpers;

  const {
    loading,
    value: documentTypes = [],
    error,
  } = useAsync(async () => {
    if (!zgwApiGroup || !catalogueUrl || !caseTypeIdentification) return [];
    return await getAvailableDocumentTypes(zgwApiGroup, catalogueUrl, caseTypeIdentification);
  }, [zgwApiGroup, catalogueUrl, caseTypeIdentification]);
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
        <ReactSelect
          name="documentTypeDescription"
          options={documentTypes}
          isLoading={loading}
          isDisabled={!zgwApiGroup || !caseTypeIdentification}
          // TODO: make required once legacy config is dropped
          required={false}
          isClearable
          components={{Option: DocumentTypeSelectOption}}
          onChange={selectedOption => {
            setValue(selectedOption ? selectedOption.value : undefined);
          }}
        />
      </Field>
    </FormRow>
  );
};

DocumentTypeSelect.propTypes = {
  catalogueUrl: PropTypes.string,
};

export default DocumentTypeSelect;
