import {groupAndSortCatalogueOptions} from 'components/admin/forms/zgw';
import {get} from 'utils/fetch';

const CATALOGUES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/catalogues';

const getCatalogues = async apiGroupID => {
  const response = await get(CATALOGUES_ENDPOINT, {zgw_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available catalogues failed');
  }
  return groupAndSortCatalogueOptions(response.data);
};

export {getCatalogues};
