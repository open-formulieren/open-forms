import {get} from 'utils/fetch';

export const getServices = async type => {
  const resp = await get(`/api/v2/services?type=${encodeURIComponent(type)}`);
  return resp.data;
};
