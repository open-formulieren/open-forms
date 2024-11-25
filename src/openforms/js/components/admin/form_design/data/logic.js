import {put} from 'utils/fetch';

const createOrUpdateLogicRules = async (formUrl, logicRules, csrftoken) => {
  const endpoint = `${formUrl}/logic-rules`;
  return await put(endpoint, csrftoken, logicRules, true);
};

export {createOrUpdateLogicRules};
