import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import Fieldset from 'components/admin/forms/Fieldset';
import {getCatalogueOption} from 'components/admin/forms/zgw';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {ConfidentialityLevel, MedewerkerRoltype, OrganisationRSIN, ProductSelect} from './fields';
import {getCatalogues} from './utils';

const OptionalOptionsFieldset = ({confidentialityLevelChoices}) => {
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="ZGW APIs registration: default overrides fieldset title"
          defaultMessage="Optional ZGW configuration"
        />
      }
      fieldNames={['organisatieRsin']}
    >
      <div className="description">
        <FormattedMessage
          description="ZGW APIs defaults override informative message"
          defaultMessage={`Any configuration option specified here overrides the
          matching option of the selected API group.`}
        />
      </div>
      <OrganisationRSIN />
      <ConfidentialityLevel options={confidentialityLevelChoices} />
      <MedewerkerRoltype />

      <ErrorBoundary
        errorMessage={
          <FormattedMessage
            description="ZGW APIs registrations options: case product error"
            defaultMessage={`Something went wrong while retrieving the available
            catalogues or products defined in the selected case. Please
            check that the services in the selected API group are configured correctly.`}
          />
        }
      >
        <CatalogiApiField />
      </ErrorBoundary>
    </Fieldset>
  );
};

const CatalogiApiField = () => {
  const {
    values: {zgwApiGroup = null, catalogue = undefined},
  } = useFormikContext();

  // fetch available catalogues and re-use the result
  const {value: catalogueOptionGroups = [], error: cataloguesError} = useAsync(async () => {
    if (!zgwApiGroup) return [];
    return await getCatalogues(zgwApiGroup);
  }, [zgwApiGroup]);
  if (cataloguesError) throw cataloguesError;

  const catalogueValue = getCatalogueOption(catalogueOptionGroups, catalogue || {});
  const catalogueUrl = catalogueValue?.url;
  return <ProductSelect catalogueUrl={catalogueUrl} />;
};

OptionalOptionsFieldset.propTypes = {
  confidentialityLevelChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
};

export default OptionalOptionsFieldset;
