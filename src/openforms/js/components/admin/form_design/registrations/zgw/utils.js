import {groupAndSortCatalogueOptions} from 'components/admin/forms/zgw';
import {get} from 'utils/fetch';

const CATALOGUES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/catalogues';
const ROLE_TYPES_ENDPOINT = '/api/v2/registration/plugins/zgw-api/role-types';

const getCatalogues = async apiGroupID => {
  const response = await get(CATALOGUES_ENDPOINT, {zgw_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available catalogues failed');
  }
  return groupAndSortCatalogueOptions(response.data);
};

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

export {getCatalogues, getAvailableRoleTypes};
