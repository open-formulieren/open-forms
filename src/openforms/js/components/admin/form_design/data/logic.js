import {put} from 'utils/fetch';

const createOrUpdateLogicRules = async (formUrl, logicRules, csrftoken, isPriceRule = false) => {
  const endpoint = isPriceRule ? `${formUrl}/price-logic-rules` : `${formUrl}/logic-rules`;
  return await put(endpoint, csrftoken, logicRules, true);
};

export {createOrUpdateLogicRules};
