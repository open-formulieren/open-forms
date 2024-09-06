import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import {useAsync} from 'react-use';

import Fieldset from 'components/admin/forms/Fieldset';
import {groupAndSortCatalogueOptions} from 'components/admin/forms/zgw';
import ErrorBoundary from 'components/errors/ErrorBoundary';
import {get} from 'utils/fetch';

import {CaseTypeSelect, CatalogueSelect, ZGWAPIGroup} from './fields';

// Data fetching

const CATALOGUES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/catalogues';

const getCatalogues = async apiGroupID => {
  const response = await get(CATALOGUES_ENDPOINT, {zgw_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available catalogues failed');
  }
  return groupAndSortCatalogueOptions(response.data);
};

// Components

const BasicOptionsFieldset = ({apiGroupChoices}) => {
  const intl = useIntl();
  const {
    values: {
      zaaktype,
      informatieobjecttype,
      medewerkerRoltype,
      propertyMappings = [],
      objecttype,
      objecttypeVersion,
      contentJson,
    },
  } = useFormikContext();

  const hasAnyFieldConfigured =
    [
      zaaktype,
      informatieobjecttype,
      medewerkerRoltype,
      objecttype,
      objecttypeVersion,
      contentJson,
    ].some(v => !!v) || propertyMappings.length > 0;

  return (
    <Fieldset>
      <ZGWAPIGroup
        apiGroupChoices={apiGroupChoices}
        onChangeCheck={() => {
          if (!hasAnyFieldConfigured) return true;
          const confirmSwitch = window.confirm(
            intl.formatMessage({
              description:
                'ZGW APIs registration options: warning message when changing the api group',
              defaultMessage: `Changing the api group will clear the existing configuration.
              Are you sure you want to continue?`,
            })
          );
          return confirmSwitch;
        }}
      />

      <ErrorBoundary
        errorMessage={
          <FormattedMessage
            description="ZGW APIs registrations options: generic error"
            defaultMessage={`Something went wrong retrieving the available catalogues
            or types defined in the selected catalogue. Please check that the services
            in the selected API group are configured correctly.`}
          />
        }
      >
        <CatalogiApiFields />
      </ErrorBoundary>
    </Fieldset>
  );
};

BasicOptionsFieldset.propTypes = {
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.number, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
};

const CatalogiApiFields = () => {
  const {values: zgwApiGroup = null} = useFormikContext();

  // fetch available catalogues and re-use the result
  const {
    loading: loadingCatalogues,
    value: catalogueOptionGroups = [],
    error: cataloguesError,
  } = useAsync(async () => {
    if (!zgwApiGroup) return [];
    return await getCatalogues(zgwApiGroup);
  }, [zgwApiGroup]);
  if (cataloguesError) throw cataloguesError;

  return (
    <>
      <CatalogueSelect loading={loadingCatalogues} optionGroups={catalogueOptionGroups} />
      <CaseTypeSelect />
    </>
  );
};

export default BasicOptionsFieldset;
