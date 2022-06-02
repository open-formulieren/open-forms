import jsonScriptToVar from '../../utils/json-script';
import {apiCall} from '../../utils/fetch';

const init = () => {
  const nodes = document.querySelectorAll('.form-category.form-category--has-children');
  if (!nodes.length) return;
  // read the original GET params so we can include them in the async calls
  const GETParams = jsonScriptToVar('request-GET');
  nodes.forEach(node => loadFormsForCategory(node, GETParams));
};

const loadFormsForCategory = async (node, GETParams) => {
  // node is a table row, after which we have to inject the forms.
  const {id, depth} = node.dataset;
  const query = new URLSearchParams({
    ...GETParams,
    _async: 1,
    category: id,
  });

  // TODO: handle pagination
  const response = await apiCall(`.?${query}`);
  const htmlBlob = await response.text();

  // create a dom element in memory to render the table, and then take out only what's
  // relevant
  const container = document.createElement('div');
  container.insertAdjacentHTML('afterbegin', htmlBlob);
  const rows = container.querySelectorAll('tbody tr');
  if (!rows.length) return;
  const fragment = document.createDocumentFragment();
  for (const row of rows) {
    row.dataset['depth'] = depth;
    row.classList.add('form-category__item');
    fragment.appendChild(row);
  }
  node.after(fragment);
};

document.addEventListener('DOMContentLoaded', () => {
  init();
});
