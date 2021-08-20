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
    // updating and creating rules
    const updateOrCreatePromises = Promise.all(
        logicRules.map(rule => {
            const shouldCreate = !rule.uuid;
            const createOrUpdate = shouldCreate ? post : put;
            const endPoint = shouldCreate ? LOGICS_ENDPOINT : `${LOGICS_ENDPOINT}/${rule.uuid}`;
            return createOrUpdate(endPoint, csrftoken, rule);
        })
    );
    // deleting rules
    const deletePromises = Promise.all(
        logicRulesToDelete
        .filter( uuid => !!uuid )
        .map( uuid => {
            return apiDelete(`${LOGICS_ENDPOINT}/${uuid}`, csrftoken);
        })
    );


    let updateOrCreateResponses, deleteResponses;
    try {
        [updateOrCreateResponses, deleteResponses] = await Promise.all([updateOrCreatePromises, deletePromises]);
    } catch(e) {
        console.error(e);
        return;
    }

    // process the created rules
    const createdRules = [];
    updateOrCreateResponses.forEach( (response, index) => {
        if (!response.ok) {
            // TODO: include more information -> which rule was it etc.
            throw new Error('An error occurred while saving the form logic.');
        }
        const rule = logicRules[index];
        if (!rule.uuid) {
            const uuid = response.data.uuid;
            createdRules.push({uuid, index});
        }
    });

    // process the deleted rules
    deleteResponses.forEach(response => {
        if (!response.ok) {
            throw new Error('An error occurred while deleting logic rules.');
        }
    });

    return createdRules;
};

export { loadPlugins, PluginLoadingError };
export { saveLogicRules };
