import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {
  ConfidentialityLevel,
  OrganisationRSIN,
  PartnersDescription,
  ProductSelect,
  RoltypeFields,
} from './fields';

const OptionalOptionsFieldset = ({confidentialityLevelChoices, catalogueUrl}) => {
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="ZGW APIs registration: default overrides fieldset title"
          defaultMessage="Optional ZGW configuration"
        />
      }
      fieldNames={[
        'organisatieRsin',
        'zaakVertrouwelijkheidaanduiding',
        'medewerkerRoltype',
        'partnersRoltype',
        'partnersDescription',
        'productUrl',
      ]}
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

      <ErrorBoundary
        errorMessage={
          <FormattedMessage
            description="ZGW APIs registrations options: role type error"
            defaultMessage={`Something went wrong while retrieving the available
            role types defined in the selected case. Please check that the services in
            the selected API group are configured correctly.`}
          />
        }
      >
        <RoltypeFields catalogueUrl={catalogueUrl} />
      </ErrorBoundary>

      <PartnersDescription />

      <ErrorBoundary
        errorMessage={
          <FormattedMessage
            description="ZGW APIs registrations options: case product error"
            defaultMessage={`Something went wrong while retrieving the available
            products defined in the selected case. Please check that the services in
            the selected API group are configured correctly.`}
          />
        }
      >
        <ProductSelect catalogueUrl={catalogueUrl} />
      </ErrorBoundary>
    </Fieldset>
  );
};

OptionalOptionsFieldset.propTypes = {
  confidentialityLevelChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(PropTypes.string) // value & label are both string
  ).isRequired,
  catalogueUrl: PropTypes.string,
};

export default OptionalOptionsFieldset;
