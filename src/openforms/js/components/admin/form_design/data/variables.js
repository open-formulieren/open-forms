import {put} from 'utils/fetch';

const createOrUpdateFormVariables = async (formUrl, variables, csrftoken) => {
  const endpoint = `${formUrl}/variables`;
  return await put(endpoint, csrftoken, variables, true);
};

export {createOrUpdateFormVariables};
