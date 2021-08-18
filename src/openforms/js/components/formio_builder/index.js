import BEM from 'bem.js';
import {BLOCK_FORM_BUILDER, ELEMENT_CONTAINER, INPUT_ELEMENT} from './constants';
import FormIOBuilder from './builder';
import React from 'react';
import ReactDOM from 'react-dom';

document.addEventListener('DOMContentLoaded', event => {
    const FORM_BUILDERS = BEM.getBEMNodes(BLOCK_FORM_BUILDER);
    [...FORM_BUILDERS].forEach(node => {

        const configurationInput = BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, INPUT_ELEMENT);
        const configuration = JSON.parse(configurationInput.value) || {display: 'form'};
        const onChange = (newConfiguration) => configurationInput.value = JSON.stringify(newConfiguration);

        ReactDOM.render(
            <FormIOBuilder configuration={configuration} onChange={onChange} />,
            BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, ELEMENT_CONTAINER)
        )
    });
});
