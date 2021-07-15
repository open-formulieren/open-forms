import React from "react";
import ReactDOM from "react-dom";
import ReactModal from 'react-modal';

import {FormCreationForm} from './form_design/form-creation-form';


const mountForm = () => {
    const formCreationFormNodes = document.getElementsByClassName('react-form-create');
    if (!formCreationFormNodes.length) return;

    for (const formCreationFormNode of formCreationFormNodes) {
        const { formUuid, formName, formSlug, csrftoken,
                formBeginText, formPreviousText, formChangeText, formConfirmText } = formCreationFormNode.dataset;

        ReactModal.setAppElement(formCreationFormNode);

        // Update this
        ReactDOM.render(
            <FormCreationForm
                csrftoken={csrftoken}
                formUuid={formUuid}
                formName={formName}
                formSlug={formSlug}
                formBeginText={formBeginText}
                formPreviousText={formPreviousText}
                formChangeText={formChangeText}
                formConfirmText={formConfirmText}
            />,
            formCreationFormNode
        );
    }
};

mountForm();
