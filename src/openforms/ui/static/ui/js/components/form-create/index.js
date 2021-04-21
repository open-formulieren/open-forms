import React from "react";
import ReactDOM from "react-dom";

import CreateForm from './form-create';


const mount = () => {
    const node = document.getElementById('react-create');
    if (!node) return;

    ReactDOM.render(
        <CreateForm />,
        node
    );
};

mount();
