import BEM from 'bem.js';

/** @const {string} */
export const BLOCK_FORMIO_FORM = 'formio-form';

/** @const {string} */
export const ELEMENT_BODY = 'body';

/** @const {NodeList} */
export const FORMIO_FORMS = BEM.getBEMNodes(BLOCK_FORMIO_FORM);
