import classNames from 'classnames';
import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import {components} from 'react-select';
import useAsync from 'react-use/esm/useAsync';

import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

const getDocumentTypes = async (endpoint, queryParams) => {
  const response = await get(endpoint, queryParams);
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

export const useGetDocumentTypes = (endpoint, queryParams) => {
  const {
    loading,
    value: documentTypes = [],
    error,
  } = useAsync(async () => {
    // abort if any query param is empty-ish
    if (Object.values(queryParams).some(v => !v)) return [];
    return await getDocumentTypes(endpoint, queryParams);
  }, [endpoint, queryParams]);

  return {loading, documentTypes, error};
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

export const DocumentTypeSelect = ({
  name,
  documentTypes = [],
  isDisabled = false,
  isRequired = false,
  isLoading,
}) => {
  const [, , {setValue}] = useField(name);
  return (
    <ReactSelect
      name={name}
      options={documentTypes}
      isLoading={isLoading}
      isDisabled={isDisabled}
      required={isRequired}
      isClearable
      components={{Option: DocumentTypeSelectOption}}
      onChange={selectedOption => {
        setValue(selectedOption ? selectedOption.value : undefined);
      }}
    />
  );
};

DocumentTypeSelect.propTypes = {
  name: PropTypes.string.isRequired,
  isLoading: PropTypes.bool.isRequired,
  documentTypes: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      isPublished: PropTypes.bool.isRequired,
    })
  ),
  isDisabled: PropTypes.bool,
  isRequired: PropTypes.bool,
};
