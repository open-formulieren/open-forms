import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import useConfirm from 'components/admin/form_design/useConfirm';
import Fieldset from 'components/admin/forms/Fieldset';
import {CatalogueSelectOptions} from 'components/admin/forms/zgw';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {CaseTypeSelect, CatalogueSelect, DocumentTypeSelect, ZGWAPIGroup} from './fields';

// Components

const BasicOptionsFieldset = ({
  apiGroupChoices,
  loadingCatalogues,
  catalogueOptionGroups = [],
  cataloguesError = undefined,
  catalogueUrl = '',
}) => {
  const {
    values: {
      caseTypeIdentification,
      documentTypeDescription,
      medewerkerRoltype,
      partnersRoltype,
      partnersDescription,
      childrenRoltype,
      childrenDescription,
      propertyMappings = [],
      objecttype,
      objecttypeVersion,
      contentJson,
    },
  } = useFormikContext();

  const hasAnyFieldConfigured =
    [
      caseTypeIdentification,
      documentTypeDescription,
      medewerkerRoltype,
      partnersRoltype,
      partnersDescription,
      childrenRoltype,
      childrenDescription,
      objecttype,
      objecttypeVersion,
      contentJson,
    ].some(v => !!v) || propertyMappings.length > 0;
  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();

  return (
    <>
      <Fieldset>
        <ZGWAPIGroup
          apiGroupChoices={apiGroupChoices}
          onChangeCheck={async () => {
            if (!hasAnyFieldConfigured) return true;
            return openConfirmationModal();
          }}
        />

        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="ZGW APIs registrations options: generic error"
              defaultMessage={`Something went wrong while retrieving the available
            catalogues or case/document types defined in the selected catalogue. Please
            check that the services in the selected API group are configured correctly.`}
            />
          }
        >
          <MaybeThrowError error={cataloguesError} />
          <CatalogueSelect loading={loadingCatalogues} optionGroups={catalogueOptionGroups} />
          <CaseTypeSelect catalogueUrl={catalogueUrl} />
          <DefaultDocumentTypeSelect catalogueUrl={catalogueUrl} />
        </ErrorBoundary>
        <ConfirmationModal
          {...confirmationModalProps}
          message={
            <FormattedMessage
              description="ZGW APIs registration options: warning message when changing the api group"
              defaultMessage="Changing the api group will clear the existing configuration.
              Are you sure you want to continue?"
            />
          }
        />
      </Fieldset>
    </>
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
  loadingCatalogues: PropTypes.bool.isRequired,
  catalogueOptionGroups: CatalogueSelectOptions.isRequired,
  cataloguesError: PropTypes.any,
  catalogueUrl: PropTypes.string,
};

/**
 * Component that only throws an error if it's not undefined, intended to trigger a
 * parent error boundary.
 */
const MaybeThrowError = ({error = undefined}) => {
  if (error) throw error;
  return null;
};

MaybeThrowError.propTypes = {
  error: PropTypes.any,
};

const DefaultDocumentTypeSelect = ({catalogueUrl = ''}) => (
  <DocumentTypeSelect
    name="documentTypeDescription"
    // TODO: make required once legacy config is dropped
    isRequired={false}
    catalogueUrl={catalogueUrl}
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
  />
);

export default BasicOptionsFieldset;
