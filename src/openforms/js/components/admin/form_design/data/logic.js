import {post, put, apiDelete} from '../../../../utils/fetch';
import {ValidationErrors} from '../../../../utils/exception';
import {LOGICS_ENDPOINT, PRICE_RULES_ENDPOINT} from '../constants';

/**
 * Generic collection of rules saving.
 *
 * This utility applies to form logic and form price rules.
 * @param  {String} endpoint           The list API endpoint
 * @param  {String} formUrl            The API resource URL for which to save the related resources
 * @param  {string} csrftoken          Cross-Site Request Forgery token value
 * @param  {Array}  rules         Array of rules to create or update, desired state
 * @param  {Array}  rulesToDelete Array of rules to delete in the backend
 * @param  {String} rulePrefix Prefix that will be used to format errors (differentiates between logic and price rules)
 * @return {Array}                     Array of newly created rules
 */
const saveRules = async (endpoint, formUrl, csrftoken, rules, rulesToDelete, rulePrefix) => {
  // updating and creating rules
  const updateOrCreatePromises = Promise.all(
    rules.map(async rule => {
      const shouldCreate = !rule.uuid;
      const createOrUpdate = shouldCreate ? post : put;
      const apiEndpoint = shouldCreate ? endpoint : `${endpoint}/${rule.uuid}`;
      try {
        return await createOrUpdate(
          apiEndpoint,
          csrftoken,
          rule.form ? rule : {...rule, form: formUrl},
          true
        );
      } catch (e) {
        return e;
      }
    })
  );
  // deleting rules
  const deletePromises = Promise.all(
    rulesToDelete
      .filter(uuid => !!uuid)
      .map(uuid => {
        return apiDelete(`${endpoint}/${uuid}`, csrftoken);
      })
  );

  let updateOrCreateResponses, deleteResponses;
  try {
    [updateOrCreateResponses, deleteResponses] = await Promise.all([
      updateOrCreatePromises,
      deletePromises,
    ]);
  } catch (e) {
    console.error(e);
    return;
  }

  // process the created/updated & errored rules
  const results = [];
  updateOrCreateResponses.forEach((response, index) => {
    if (response instanceof ValidationErrors) {
      // rewrite so the correct name/index is used for the error information
      response.errors = response.errors.map((err, _) => {
        return {
          ...err,
          name: [rulePrefix, index, err.name].join('.'),
        };
      });
      response.context = rulePrefix;
    }
    // TODO: handle non-validation errors?
    results.push(response);
  });

  // process the deleted rules
  // TODO: more gracious handling, and have we ever seen this even?
  deleteResponses.forEach(response => {
    if (!response.ok) {
      throw new Error('An error occurred while deleting logic rules.');
    }
  });

  return results;
};

const saveLogicRules = async (formUrl, csrftoken, logicRules, logicRulesToDelete) => {
  const results = await saveRules(
    LOGICS_ENDPOINT,
    formUrl,
    csrftoken,
    logicRules,
    logicRulesToDelete,
    'logicRules'
  );
  return results;
};

const savePriceRules = async (formUrl, csrftoken, priceRules, priceRulesToDelete) => {
  const results = await saveRules(
    PRICE_RULES_ENDPOINT,
    formUrl,
    csrftoken,
    priceRules,
    priceRulesToDelete,
    'priceRules'
  );
  return results;
};

export {saveLogicRules, savePriceRules};
