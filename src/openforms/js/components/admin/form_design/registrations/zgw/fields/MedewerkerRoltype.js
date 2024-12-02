import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

// Data fetching

const ROLE_TYPES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/role-types';

const getAvailableRoleTypes = async (apiGroupID, catalogueUrl, caseTypeIdentification) => {
  const response = await get(ROLE_TYPES_ENDPOINT, {
    zgw_api_group: apiGroupID,
    catalogue_url: catalogueUrl,
    case_type_identification: caseTypeIdentification,
  });
  if (!response.ok) {
    throw new Error('Loading available object types failed');
  }
  const roleTypes = response.data.sort((a, b) => a.description.localeCompare(b.description));
  return roleTypes.map(({description, descriptionGeneric}) => ({
    value: description,
    label: description,
    descriptionGeneric: descriptionGeneric, // omschrijvingGeneriek, which is an enum
  }));
};

// Components

/**
 * @deprecated
 */
const MedewerkerRoltypeLegacy = () => {
  const [fieldProps] = useField('medewerkerRoltype');
  return <TextInput id="id_medewerkerRoltype" {...fieldProps} />;
};

const MedewerkerRoltypeSelect = ({catalogueUrl = ''}) => {
  const {
    values: {zgwApiGroup = null, caseTypeIdentification = ''},
  } = useFormikContext();
  const [, , fieldHelpers] = useField('medewerkerRoltype');
  const {setValue} = fieldHelpers;

  const {
    loading,
    value: roleTypes = [],
    error,
  } = useAsync(async () => {
    if (!zgwApiGroup || !catalogueUrl || !caseTypeIdentification) return [];
    return await getAvailableRoleTypes(zgwApiGroup, catalogueUrl, caseTypeIdentification);
  }, [zgwApiGroup, catalogueUrl, caseTypeIdentification]);
  if (error) throw error;

  return (
    <ReactSelect
      name="medewerkerRoltype"
      options={roleTypes}
      isLoading={loading}
      isDisabled={!zgwApiGroup || !caseTypeIdentification}
      required={false}
      isClearable
      onChange={selectedOption => {
        setValue(selectedOption ? selectedOption.value : '');
      }}
    />
  );
};

MedewerkerRoltypeSelect.propTypes = {
  catalogueUrl: PropTypes.string,
};

const MedewerkerRoltype = ({catalogueUrl = ''}) => {
  const {
    values: {caseTypeIdentification = '', zaaktype = ''},
  } = useFormikContext();
  // render legacy field if a case type URL is used instead of a identification reference
  const renderLegacy = !!zaaktype && !caseTypeIdentification;
  return (
    <FormRow>
      <Field
        name="medewerkerRoltype"
        label={
          <FormattedMessage
            description="Objects API registration options 'medewerkerRoltype' label"
            defaultMessage="Medewerker roltype"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration options 'medewerkerRoltype' help text"
            defaultMessage={`Description (omschrijving) of the ROLTYPE to use for
            employees filling in a form for a citizen/company.`}
          />
        }
        noManageChildProps
      >
        {renderLegacy ? (
          <MedewerkerRoltypeLegacy />
        ) : (
          <MedewerkerRoltypeSelect catalogueUrl={catalogueUrl} />
        )}
      </Field>
    </FormRow>
  );
};

MedewerkerRoltype.propTypes = {
  catalogueUrl: PropTypes.string,
};

export default MedewerkerRoltype;
