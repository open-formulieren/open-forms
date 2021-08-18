import {get} from '../../../utils/fetch';

class PluginLoadingError extends Error {
    constructor(message, plugin, response) {
        super(message);
        this.plugin = plugin;
        this.response = response;
    }
};


// TODO: add error handling in the fetch wrappers to throw exceptions + add error
// boundaries in the component tree.
const loadPlugins = async (plugins=[]) => {
    const promises = plugins.map(async (plugin) => {
        let response = await get(plugin.endpoint);
        if (!response.ok) {
            throw new PluginLoadingError('Failed to load plugins', plugin, response);
        }
        let responseData = response.data;

        // paginated or not?
        const isPaginated = responseData.hasOwnProperty('results') && responseData.hasOwnProperty('count');
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
                throw new PluginLoadingError('Failed to load plugins', plugin, response);
            }
            responseData = response.data;
            allResults = [...allResults, ...responseData.results];
        }
        return allResults;
    });
    const results = await Promise.all(promises);
    return results;
};

export { loadPlugins, PluginLoadingError };
