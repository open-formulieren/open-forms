import {useFormikContext} from 'formik';
import {useAsync, usePrevious, useUpdateEffect} from 'react-use';

import {getCatalogueOption} from 'components/admin/forms/zgw';

import {getCatalogues} from './utils';

/**
 * Hook that manages everything related to the ZGW API group available catalogues.
 *
 * It's responsible for retrieving the options and the derived catalogueUrl if a
 * catalogue is selected. It also takes care of resetting dependent form state if the
 * catalogue changes.
 */
const useCatalogueOptions = () => {
  const {
    values: {
      zgwApiGroup = null,
      catalogue = undefined,
      caseTypeIdentification = '',
      documentTypeDescription = '',
      medewerkerRoltype = '',
      partnersRoltype = '',
      childrenRoltype = '',
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

  // 4. Clear roltypen when case type changes
  useUpdateEffect(() => {
    const caseTypeChanged = caseTypeIdentification !== previousCaseTypeIdentification;
    if (previousCaseTypeIdentification && caseTypeChanged) {
      if (medewerkerRoltype) {
        setFieldValue('medewerkerRoltype', '');
      }
      if (partnersRoltype) {
        setFieldValue('partnersRoltype', '');
      }
      if (childrenRoltype) {
        setFieldValue('childrenRoltype', '');
      }
    }
  }, [
    setFieldValue,
    previousCaseTypeIdentification,
    caseTypeIdentification,
    medewerkerRoltype,
    partnersRoltype,
    childrenRoltype,
  ]);

  return {
    loadingCatalogues,
    catalogueOptionGroups,
    cataloguesError,
    catalogueUrl,
  };
};

export default useCatalogueOptions;
