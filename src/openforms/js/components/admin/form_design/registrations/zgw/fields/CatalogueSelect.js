import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {
  CatalogueSelect as GenericCatalogueSelect,
  groupAndSortCatalogueOptions,
} from 'components/admin/forms/zgw';
import {get} from 'utils/fetch';

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

const CatalogueSelect = () => {
  const {values} = useFormikContext();
  const {zgwApiGroup = null} = values;

  // fetch available catalogues
  const {
    loading: loadingCatalogues,
    value: catalogueOptionGroups = [],
    error: cataloguesError,
  } = useAsync(async () => {
    if (!zgwApiGroup) return [];
    return await getCatalogues(zgwApiGroup);
  }, [zgwApiGroup]);
  if (cataloguesError) throw cataloguesError;

  // TODO: make required when case type can be selected in a dropdown AND there is no
  // legacy case type or document type URL specified. Probably best to do this as
  // backend validation so that new registration backends must select a catalogue.
  return (
    <GenericCatalogueSelect
      label={
        <FormattedMessage
          description="ZGW APIs registration options 'catalogue' label"
          defaultMessage="Catalogue"
        />
      }
      isDisabled={!zgwApiGroup}
      loading={loadingCatalogues}
      optionGroups={catalogueOptionGroups}
    />
  );
};

CatalogueSelect.propTypes = {};

export default CatalogueSelect;
