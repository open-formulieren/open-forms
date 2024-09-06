import classNames from 'classnames';
import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
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
    label: (
      <span
        className={classNames('case-type-option', {
          'case-type-option--draft': !isPublished,
        })}
      >
        <FormattedMessage
          description="Case type option label"
          defaultMessage={`{description} {isPublished, select, false {<draft>(not published)</draft>} other {}}`}
          values={{
            description,
            isPublished,
            draft: chunks => <span className="case-type-option__draft-suffix">{chunks}</span>,
          }}
        />
      </span>
    ),
  }));
};

const CaseTypeSelect = ({catalogueUrl}) => {
  const [fieldProps, , fieldHelpers] = useField('case_type_identification');
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
    if (!zgwApiGroup) return [];
    return await getAvailableCaseTypes(zgwApiGroup, catalogueUrl);
  }, [zgwApiGroup, catalogueUrl]);
  if (error) throw error;

  return (
    <FormRow>
      <Field
        name="case_type_identification"
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
          name="case_type_identification"
          options={caseTypes}
          isLoading={loading}
          isDisabled={!zgwApiGroup}
          // TODO: make required once legacy config is dropped
          required={false}
          isClearable
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
