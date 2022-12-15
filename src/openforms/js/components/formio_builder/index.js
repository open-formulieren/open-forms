import BEM from 'bem.js';
import flatpickr from 'flatpickr';
import {Dutch} from 'flatpickr/dist/l10n/nl.js';
import React from 'react';
import ReactDOM from 'react-dom';

import {onLoaded} from 'utils/dom';

import FormIOBuilder from './builder';
import {BLOCK_FORM_BUILDER, ELEMENT_CONTAINER, INPUT_ELEMENT} from './constants';

onLoaded(() => {
  const FORM_BUILDERS = BEM.getBEMNodes(BLOCK_FORM_BUILDER);
  [...FORM_BUILDERS].forEach(node => {
    const configurationInput = BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, INPUT_ELEMENT);
    const configuration = JSON.parse(configurationInput.value) || {display: 'form'};
    const onChange = newConfiguration =>
      (configurationInput.value = JSON.stringify(newConfiguration));

    ReactDOM.render(
      <FormIOBuilder configuration={configuration} onChange={onChange} />,
      BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, ELEMENT_CONTAINER)
    );
  });

  initFlatpickr();
});

const initFlatpickr = () => {
  flatpickr.localize(Dutch);
};
