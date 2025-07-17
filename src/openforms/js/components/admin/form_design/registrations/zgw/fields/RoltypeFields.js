import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';

import {getAvailableRoleTypes} from '../utils';

// Components

/**
 * @deprecated
 */
const MedewerkerRoltypeLegacy = () => {
  const [fieldProps] = useField('medewerkerRoltype');
  return <TextInput id="id_medewerkerRoltype" {...fieldProps} />;
};

const MedewerkerRoltypeSelect = ({roltypes, loading, zgwApiGroup, caseTypeIdentification}) => {
  const [, , fieldHelpers] = useField('medewerkerRoltype');
  const {setValue} = fieldHelpers;

  return (
    <ReactSelect
      name="medewerkerRoltype"
      options={roltypes}
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

const PartnersRoltypeSelect = ({roltypes, loading, zgwApiGroup, caseTypeIdentification}) => {
  const [, , fieldHelpers] = useField('partnersRoltype');
  const {setValue} = fieldHelpers;

  return (
    <ReactSelect
      name="partnersRoltype"
      options={roltypes}
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

PartnersRoltypeSelect.propTypes = {
  catalogueUrl: PropTypes.string,
};

const RoltypeFields = ({catalogueUrl = ''}) => {
  const {
    values: {zgwApiGroup = null, caseTypeIdentification = '', zaaktype = ''},
  } = useFormikContext();
  // render legacy field if a case type URL is used instead of a identification reference
  const renderLegacy = !!zaaktype && !caseTypeIdentification;

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
    <>
      <FormRow>
        <Field
          name="medewerkerRoltype"
          label={
            <FormattedMessage
              description="ZGW-APIs registration options 'medewerkerRoltype' label"
              defaultMessage="Medewerker roltype"
            />
          }
          helpText={
            <FormattedMessage
              description="ZGW-APIs registration options 'medewerkerRoltype' help text"
              defaultMessage={`Description (omschrijving) of the ROLTYPE to use for
            employees filling in a form for a citizen/company.`}
            />
          }
          noManageChildProps
        >
          {renderLegacy ? (
            <MedewerkerRoltypeLegacy />
          ) : (
            <MedewerkerRoltypeSelect
              roltypes={roleTypes}
              loading={loading}
              zgwApiGroup={zgwApiGroup}
              caseTypeIdentification={caseTypeIdentification}
            />
          )}
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="partnersRoltype"
          label={
            <FormattedMessage
              description="ZGW-APIs registration options 'partnersRoltype' label"
              defaultMessage="Partners roltype"
            />
          }
          helpText={
            <FormattedMessage
              description="ZGW-APIs registration options 'partnersRoltype' help text"
              defaultMessage={`Description (omschrijving) of the ROLTYPE to use for citizens
                filling in a form with partners.`}
            />
          }
          noManageChildProps
        >
          <PartnersRoltypeSelect
            roltypes={roleTypes}
            loading={loading}
            zgwApiGroup={zgwApiGroup}
            caseTypeIdentification={caseTypeIdentification}
          />
        </Field>
      </FormRow>
    </>
  );
};

RoltypeFields.propTypes = {
  catalogueUrl: PropTypes.string,
};

export default RoltypeFields;
