import React from "react";
import ReactDOM from "react-dom";

import EditForm from './form-edit';


const mount = () => {
    const node = document.getElementById('react-edit');
    const formUuid = document.getElementById('form-uuid').innerHTML;
    if (!node || !formUuid) return;


    // TODO Pass props here, see https://github.com/open-formulieren/open-forms-sdk/blob/main/src/sdk.js#L32
    ReactDOM.render(
        <EditForm />,
        node
    );
};

mount();
