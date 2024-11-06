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

const CASE_TYPES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/case-types';

const getAvailableCaseTypes = async (apiGroupID, catalogueUrl) => {
  const response = await get(CASE_TYPES_ENDPOINT, {
    zgw_api_group: apiGroupID,
    catalogue_url: catalogueUrl,
  });
  if (!response.ok) {
    throw new Error('Loading available object types failed');
  }
  const caseTypes = response.data.sort((a, b) => a.description.localeCompare(b.description));
  return caseTypes.map(({identification, description, isPublished}) => ({
    value: identification,
    label: description,
    isPublished: isPublished,
  }));
};

// Components

const CaseTypeSelectOption = props => {
  const {isPublished, label} = props.data;
  return (
    <components.Option {...props}>
      <span
        className={classNames('catalogi-type-option', {
          'catalogi-type-option--draft': !isPublished,
        })}
      >
        <FormattedMessage
          description="Case type option label"
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

const CaseTypeSelect = ({catalogueUrl = ''}) => {
  const [fieldProps, , fieldHelpers] = useField('caseTypeIdentification');
  const {
    values: {zgwApiGroup = null},
  } = useFormikContext();
  const {value} = fieldProps;
  const {setValue} = fieldHelpers;

  const {
    loading,
    value: caseTypes = [],
    error,
  } = useAsync(async () => {
    if (!zgwApiGroup || !catalogueUrl) return [];
    return await getAvailableCaseTypes(zgwApiGroup, catalogueUrl);
  }, [zgwApiGroup, catalogueUrl]);
  if (error) throw error;

  return (
    <FormRow>
      <Field
        name="caseTypeIdentification"
        // TODO: make required once legacy config is dropped
        required={false}
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'case type' label"
            defaultMessage="Case type"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'case type' helpText"
            defaultMessage="A case of this type will be created during registration."
          />
        }
        noManageChildProps
      >
        <ReactSelect
          name="caseTypeIdentification"
          options={caseTypes}
          isLoading={loading}
          isDisabled={!zgwApiGroup}
          // TODO: make required once legacy config is dropped
          required={false}
          isClearable
          components={{Option: CaseTypeSelectOption}}
          onChange={selectedOption => {
            setValue(selectedOption ? selectedOption.value : undefined);
          }}
        />
      </Field>
    </FormRow>
  );
};

CaseTypeSelect.propTypes = {
  catalogueUrl: PropTypes.string,
};

export default CaseTypeSelect;
