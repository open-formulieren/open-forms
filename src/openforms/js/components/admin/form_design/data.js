import {FormException} from '../../../utils/exception';
import {get, post, put, apiDelete, ValidationErrors} from '../../../utils/fetch';
import {
    FORM_DEFINITIONS_ENDPOINT,
    LOGICS_ENDPOINT,
    PRICE_RULES_ENDPOINT,
} from './constants';
import {saveRules} from './logic-data';

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


const updateOrCreateSingleFormStep = async (csrftoken, index, formUrl, step) => {
    // First update/create the form definitions
    const isNewFormDefinition = !!step.formDefinition;
    const definitionCreateOrUpdate = isNewFormDefinition ? put : post;
    const definitionEndpoint = step.formDefinition ? step.formDefinition : `${FORM_DEFINITIONS_ENDPOINT}`;

    const definitionData = {
        name: step.name,
        internalName: step.internalName,
        slug: step.slug,
        configuration: step.configuration,
        loginRequired: step.loginRequired,
        isReusable: step.isReusable,
    };

    try {
        var definitionResponse = await definitionCreateOrUpdate(definitionEndpoint, csrftoken, definitionData, true);
        // handle any unexpected API errors
        if (!definitionResponse.ok) {
            throw new FormException(
                'An error occurred while updating the form definitions',
                definitionResponse.data
            );
        }
    } catch (e) {
        // re-throw both expected validation errors and unexpected errors, calling code
        // deals with it. We must abort here, since the dependent formStep cannot continue
        // if this fails.
        throw e;
    }

    // okay, form definition create-update succeeded, let's proceed...
    const stepCreateOrUpdate = step.url ? put : post;
    const stepEndpoint = step.url ? step.url : `${formUrl}/steps`;
    const stepData = {
        index: index,
        formDefinition: definitionResponse.data.url,
        literals: {
            nextText: {
                value: step.literals.nextText.value
            },
            saveText: {
                value: step.literals.saveText.value
            },
            previousText: {
                value: step.literals.previousText.value
            },
        }
    };

    try {
        var stepResponse = await stepCreateOrUpdate(stepEndpoint, csrftoken, stepData, true);
        // handle any unexpected API errors
        if (!stepResponse.ok) {
            throw new FormException(
                'An error occurred while updating the form steps.',
                stepResponse.data
            );
        }
    } catch(e) {
        // re-throw both expected validation errors and unexpected errors, calling code
        // deals with it.
        throw e;
    }
};


/**
 * Update (or create) all the form step configurations.
 *
 * Validation errors raised for each individual step are caught and returned to the
 * caller.
 */
const updateOrCreateFormSteps = async (csrftoken, formUrl, formSteps) => {
    const stepPromises = formSteps.map( async (step, index) => {
        try {
            await updateOrCreateSingleFormStep(csrftoken, index, formUrl, step);
            return null;
        } catch (e) {
            if (e instanceof ValidationErrors) {
                return {
                    step: step,
                    error: e,
                };
            }
            throw e; // re-throw unexpected errors
        }
    });
    return (await Promise.all(stepPromises));
};


const saveLogicRules = async (formUrl, csrftoken, logicRules, logicRulesToDelete) => {
    const createdRules = await saveRules(
        LOGICS_ENDPOINT,
        formUrl,
        csrftoken,
        logicRules,
        logicRulesToDelete,
        'logicRules',
    );
    return createdRules;
};


const savePriceRules = async (formUrl, csrftoken, priceRules, priceRulesToDelete) => {
    const createdRules = await saveRules(
        PRICE_RULES_ENDPOINT,
        formUrl,
        csrftoken,
        priceRules,
        priceRulesToDelete,
        'priceRules',
    );
    return createdRules;
};


export { loadPlugins, PluginLoadingError };
export { updateOrCreateFormSteps };
export { saveLogicRules, savePriceRules };
