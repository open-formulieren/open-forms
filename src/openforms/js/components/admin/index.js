import React from 'react';
import ReactDOM from 'react-dom';
import ReactModal from 'react-modal';
import {IntlProvider} from 'react-intl';

import {FormCreationForm} from './form_design/form-creation-form';
import {TinyMceContext} from './form_design/Context';
import FormVersionsTable from './form_versions/FormVersionsTable';
import './sdk-snippet';

const messages = {
    nl: {},
};

const lang = document.querySelector('html').getAttribute("lang");

const mountForm = () => {
    const formCreationFormNodes = document.getElementsByClassName('react-form-create');
    if (!formCreationFormNodes.length) return;

    for (const formCreationFormNode of formCreationFormNodes) {
        const { csrftoken, formUuid, tinymceUrl, formHistoryUrl } = formCreationFormNode.dataset;

        ReactModal.setAppElement(formCreationFormNode);

        ReactDOM.render(
            <IntlProvider messages={messages[lang]} locale={lang} defaultLocale="en">
                <TinyMceContext.Provider value={tinymceUrl}>
                    <FormCreationForm csrftoken={csrftoken} formUuid={formUuid} formHistoryUrl={formHistoryUrl} />
                </TinyMceContext.Provider>
            </IntlProvider>,
            formCreationFormNode
        );
    }
};

const mountFormVersions = () => {
    const formVersionsNodes = document.getElementsByClassName('react-form-versions-table');
    if (!formVersionsNodes.length) return;

    for (const formVersionsNode of formVersionsNodes) {
        const { formUuid, csrftoken, formAdminUrl } = formVersionsNode.dataset;

        ReactDOM.render(
            <IntlProvider messages={messages[lang]} locale={lang} defaultLocale="en">
                <FormVersionsTable
                    csrftoken={csrftoken}
                    formUuid={formUuid}
                    formAdminUrl={formAdminUrl}
                />
            </IntlProvider>,
            formVersionsNode
        );
    }
};

mountForm();
mountFormVersions();
