import React from "react";
import ReactDOM from "react-dom";
import ReactModal from 'react-modal';

import {FormCreationForm} from './form_design/form-creation-form';
import {TinyMceContext} from './form_design/Context';


const mountForm = () => {
    const formCreationFormNodes = document.getElementsByClassName('react-form-create');
    if (!formCreationFormNodes.length) return;

    for (const formCreationFormNode of formCreationFormNodes) {
        const { formUuid, formName, formSlug, csrftoken, tinymceUrl,
                formBeginText, formPreviousText, formChangeText, formConfirmText } = formCreationFormNode.dataset;

        ReactModal.setAppElement(formCreationFormNode);

        ReactDOM.render(
            <TinyMceContext.Provider value={tinymceUrl}>
                <FormCreationForm
                    csrftoken={csrftoken}
                    formUuid={formUuid}
                    formName={formName}
                    formSlug={formSlug}
                    formBeginText={formBeginText}
                    formPreviousText={formPreviousText}
                    formChangeText={formChangeText}
                    formConfirmText={formConfirmText}
                />
            </TinyMceContext.Provider>,
            formCreationFormNode
        );
    }
};

mountForm();
