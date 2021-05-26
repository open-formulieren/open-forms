import React from "react";
import ReactDOM from "react-dom";
import {FormCreationForm} from './form-creation-form';

const mountForm = () => {
    const formCreationFormNodes = document.getElementsByClassName('react-form-create');
    if (!formCreationFormNodes.length) return;

    for (const formCreationFormNode of formCreationFormNodes) {
        const { formUuid, formName, formSlug, csrftoken } = formCreationFormNode.dataset;

        ReactDOM.render(
            <FormCreationForm
                csrftoken={csrftoken}
                formUuid={formUuid}
                formName={formName}
                formSlug={formSlug}
            />,
            formCreationFormNode
        );
    }
};

mountForm();
