import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import {useAsync, usePrevious, useUpdateEffect} from 'react-use';

import useConfirm from 'components/admin/form_design/useConfirm';
import Fieldset from 'components/admin/forms/Fieldset';
import {getCatalogueOption} from 'components/admin/forms/zgw';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {CaseTypeSelect, CatalogueSelect, DocumentTypeSelect, ZGWAPIGroup} from './fields';
import {getCatalogues} from './utils';

// Components

const BasicOptionsFieldset = ({apiGroupChoices}) => {
  const {
    values: {
      caseTypeIdentification,
      documentTypeDescription,
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
      caseTypeIdentification,
      documentTypeDescription,
      zaaktype,
      informatieobjecttype,
      medewerkerRoltype,
      objecttype,
      objecttypeVersion,
      contentJson,
    ].some(v => !!v) || propertyMappings.length > 0;
  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();

  return (
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
        <CatalogiApiFields />
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
  const {
    values: {
      zgwApiGroup = null,
      catalogue = undefined,
      caseTypeIdentification = '',
      documentTypeDescription = '',
      productUrl = '',
    },
    setFieldValue,
  } = useFormikContext();

  const previousCatalogue = usePrevious(catalogue);
  const previousCaseTypeIdentification = usePrevious(caseTypeIdentification);

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

  const catalogueValue = getCatalogueOption(catalogueOptionGroups, catalogue || {});
  const catalogueUrl = catalogueValue?.url;

  // Synchronize dependent fields when dependencies change.
  // 1. Clear case type when catalogue changes.
  useUpdateEffect(() => {
    const catalogueChanged = catalogue !== previousCatalogue;
    if (previousCatalogue && catalogueChanged && caseTypeIdentification) {
      setFieldValue('caseTypeIdentification', '');
    }
  }, [setFieldValue, previousCatalogue, catalogue, caseTypeIdentification]);

  // 2. Clear document type when case type changes
  useUpdateEffect(() => {
    const caseTypeChanged = caseTypeIdentification !== previousCaseTypeIdentification;
    if (previousCaseTypeIdentification && caseTypeChanged && documentTypeDescription) {
      setFieldValue('documentTypeDescription', '');
    }
  }, [
    setFieldValue,
    previousCaseTypeIdentification,
    caseTypeIdentification,
    documentTypeDescription,
  ]);

  // 3. Clear selected product when case type changes
  useUpdateEffect(() => {
    const caseTypeChanged = caseTypeIdentification !== previousCaseTypeIdentification;
    if (previousCaseTypeIdentification && caseTypeChanged && productUrl) {
      setFieldValue('productUrl', '');
    }
  }, [setFieldValue, previousCaseTypeIdentification, caseTypeIdentification, productUrl]);

  return (
    <>
      <CatalogueSelect loading={loadingCatalogues} optionGroups={catalogueOptionGroups} />
      <CaseTypeSelect catalogueUrl={catalogueUrl} />
      <DocumentTypeSelect catalogueUrl={catalogueUrl} />
    </>
  );
};

export default BasicOptionsFieldset;
