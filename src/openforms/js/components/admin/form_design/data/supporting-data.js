import {get} from 'utils/fetch';

class BackendLoadingError extends Error {
  constructor(message, specification, response) {
    super(message);
    this.specification = specification;
    this.response = response;
  }
}

// TODO: add error handling in the fetch wrappers to throw exceptions + add error
// boundaries in the component tree.
const loadFromBackend = async (specifications = []) => {
  const promises = specifications.map(async specification => {
    const {endpoint, query = {}, reshapeData = null} = specification;
    let response = await get(endpoint, query);
    if (!response.ok) {
      throw new BackendLoadingError('Failed to load specifications', specification, response);
    }
    let responseData = response.data;

    // paginated or not?
    const isPaginated =
      responseData.hasOwnProperty('results') && responseData.hasOwnProperty('count');
    if (!isPaginated) {
      return responseData;
    }

    // yep, resolve all pages
    // TODO: check if we have endpoints that return stupid amounts of data and treat those
    // differently/async to reduce the browser memory footprint
    let allResults = [...responseData.results];
    while (responseData.next) {
      response = await get(responseData.next);
      if (!response.ok) {
        throw new BackendLoadingError('Failed to load specifications', specification, response);
      }
      responseData = response.data;
      allResults = [...allResults, ...responseData.results];
    }

    if (reshapeData) allResults = reshapeData(allResults);

    return allResults;
  });
  const results = await Promise.all(promises);
  return results;
};

export {loadFromBackend, BackendLoadingError};
