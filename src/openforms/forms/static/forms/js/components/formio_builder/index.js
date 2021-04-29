import BEM from "bem.js";
import {BLOCK_FORM_BUILDER, ELEMENT_CONTAINER} from "./constants";
import FormIOBuilder from "./builder";
import React from "react";
import ReactDOM from "react-dom";

document.addEventListener("DOMContentLoaded", event => {
    const FORM_BUILDERS = BEM.getBEMNodes(BLOCK_FORM_BUILDER);
    [...FORM_BUILDERS].forEach(node => {
        ReactDOM.render(
            <FormIOBuilder node={node} />,
            BEM.getChildBEMNode(node, BLOCK_FORM_BUILDER, ELEMENT_CONTAINER)
        )
    });
});
