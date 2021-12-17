import {post, put, apiDelete, ValidationErrors} from '../../../utils/fetch';
import {LOGICS_ENDPOINT} from './constants';

/**
 * Generic collection of rules saving.
 *
 * This utility applies to form logic and form price rules.
 * @param  {String} endpoint           The list API endpoint
 * @param  {String} formUrl            The API resource URL for which to save the related resources
 * @param  {string} csrftoken          Cross-Site Request Forgery token value
 * @param  {Array}  rules         Array of rules to create or update, desired state
 * @param  {Array}  rulesToDelete Array of rules to delete in the backend
 * @return {Array}                     Array of newly created rules
 */
export const saveRules = async (endpoint, formUrl, csrftoken, rules, rulesToDelete) => {
    const fieldPrefix = endpoint === LOGICS_ENDPOINT ? 'logicRules' : 'priceRules';
    // updating and creating rules
    const updateOrCreatePromises = Promise.all(
        rules.map(rule => {
            const shouldCreate = !rule.uuid;
            const createOrUpdate = shouldCreate ? post : put;
            const endPoint = shouldCreate ? endpoint : `${endpoint}/${rule.uuid}`;

            return createOrUpdate(endPoint, csrftoken, rule.form ? rule : {...rule, form: formUrl});
        })
    );
    // deleting rules
    const deletePromises = Promise.all(
        rulesToDelete
        .filter( uuid => !!uuid )
        .map( uuid => {
            return apiDelete(`${endpoint}/${uuid}`, csrftoken);
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
            if (response.status === 400) {
                let errors = [...response.data.invalidParams].map((err, _) => {
                    return {
                        ...err,
                        name: `${fieldPrefix}.${index}.${err.name}`,
                    };
                });
                throw new ValidationErrors(
                    'Invalid logic rule',
                    errors,
                );
            } else {
                // TODO: include more information -> which rule was it etc.
                throw new Error('An error occurred while saving the form logic.');
            }
        }
        const rule = rules[index];
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
