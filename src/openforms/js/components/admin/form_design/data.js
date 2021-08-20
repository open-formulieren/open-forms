import {get, post, put, apiDelete} from '../../../utils/fetch';
import {LOGICS_ENDPOINT} from './constants';

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

const saveLogicRules = async (csrftoken, logicRules, logicRulesToDelete) => {
    const createdRules = [];

    for (const logicRule of logicRules) {
        const isNewRule = !logicRule.uuid;
        const createOrUpdate = isNewRule ? post : put;
        const endPoint = isNewRule ? LOGICS_ENDPOINT : `${LOGICS_ENDPOINT}/${logicRule.uuid}`;

        var formLogicResponse = await createOrUpdate(
            endPoint,
            csrftoken,
            logicRule
        );

        if (!formLogicResponse.ok) {
            throw new Error('An error occurred while saving the form logic.');
        }

        var ruleUuid = formLogicResponse.data.uuid;
        if (isNewRule) {
            createdRules.push({
                uuid: ruleUuid,
                index: logicRules.indexOf(logicRule)
            });
        }
    }

    // Rules that were added but are not saved in the backend yet don't have a UUID.
    const uuidsToDelete = logicRulesToDelete.map(uuid => Boolean(uuid));

    for (const ruleUuid of uuidsToDelete) {
        const response = await apiDelete(`${LOGICS_ENDPOINT}/${ruleUuid}`, csrftoken);
        if (!response.ok) {
            throw new Error('An error occurred while deleting logic rules.');
        }
    }

    return createdRules;
};

export { loadPlugins, PluginLoadingError };
export { saveLogicRules };
