import React from "react";
import ReactDOM from "react-dom";

import EditForm from './form-edit';


const mount = () => {
    const node = document.getElementById('react-edit');
    if (!node) return;


    // TODO Pass props here, see https://github.com/open-formulieren/open-forms-sdk/blob/main/src/sdk.js#L32
    ReactDOM.render(
        <EditForm />,
        node
    );
};

mount();
