import {get} from 'utils/fetch';

export const getServices = async type => {
  const resp = await get(`/api/v2/services?type=${encodeURIComponent(type)}`);
  return resp.data;
};

export const getReferentielijstenTabellen = async service => {
  const resp = await get(`/api/v2/referentielijst-tabellen/${service}`);
  return resp.data;
};
