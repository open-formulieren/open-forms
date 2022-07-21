import {post} from 'utils/fetch';

const createFormVersion = async (formUrl, csrftoken) => {
  const endpoint = `${formUrl}/versions`;
  return await post(endpoint, csrftoken, {}, true);
};

export {createFormVersion};
