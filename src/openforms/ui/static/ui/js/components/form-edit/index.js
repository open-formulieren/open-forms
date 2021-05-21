import React from "react";
import ReactDOM from "react-dom";

import EditForm from './form-edit';


const mount = () => {
    const node = document.getElementById('react-edit');
    const formUuid = document.getElementById('form-uuid').innerHTML;
    if (!node || !formUuid) return;

    ReactDOM.render(
        <EditForm formUUID={formUuid}/>,
        node
    );
};

mount();
