/**
 * Implement the API calls to fetch the data for a given form.
 */
import {FORM_ENDPOINT} from 'components/admin/form_design/constants';
import {get} from 'utils/fetch';

const loadForm = async formUuid => {
  // no UUID -> it's an empty, new form
  if (!formUuid) {
    return {steps: []};
  }

  // do all the requests in parallel
  const requests = [
    get(`${FORM_ENDPOINT}/${formUuid}`),
    get(`${FORM_ENDPOINT}/${formUuid}/steps`),
    get(`${FORM_ENDPOINT}/${formUuid}/variables`),
  ];

  const responses = await Promise.all(requests);
  if (responses.some(response => !response.ok)) {
    throw new Error('An error occurred while loading the form data.');
  }

  const [formResponse, formStepsResponse, formVariablesResponse] = responses;
  const {literals, ...form} = formResponse.data;

  return {
    form,
    literals,
    selectedAuthPlugins: form.loginOptions.map((plugin, index) => plugin.identifier),
    steps: formStepsResponse.data,
    variables: formVariablesResponse.data,
  };
};

export default loadForm;
