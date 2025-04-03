import {get} from 'utils/fetch';

export const getServices = async type => {
  const resp = await get(`/api/v2/services`, {type: type});
  return resp.data;
};

export const getReferenceListsTables = async service => {
  const resp = await get(`/api/v2/reference-lists-tables/${service}`);
  return resp.data;
};

export const getReferenceListsTableItems = async (service, tableCode) => {
  const resp = await get(`/api/v2/reference-lists-tables/${service}/${tableCode}/table-items`);
  return resp.data;
};
