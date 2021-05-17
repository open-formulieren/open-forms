import React from "react";
import ReactDOM from "react-dom";

import EditForm from './form-edit';


const mount = () => {
    const node = document.getElementById('react-edit');
    if (!node) return;

    ReactDOM.render(
        <EditForm />,
        node
    );
};

mount();
