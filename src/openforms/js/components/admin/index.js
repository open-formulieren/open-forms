import React from 'react';
import ReactDOM from 'react-dom';
import ReactModal from 'react-modal';
import {IntlProvider} from 'react-intl';

import {FormCreationForm} from './form_design/form-creation-form';
import {TinyMceContext} from './form_design/Context';
import FormVersionsTable from './form_versions/FormVersionsTable';
import './sdk-snippet';

import Debug from './debug';

const loadLocaleData = (locale) => {
    switch (locale) {
        case 'nl':
            return import('../../compiled-lang/nl.json');
        default:
            return import('../../compiled-lang/en.json');
    }
};

const mountForm = (locale, messages) => {
    const formCreationFormNodes = document.getElementsByClassName('react-form-create');
    if (!formCreationFormNodes.length) return;

    for (const formCreationFormNode of formCreationFormNodes) {
        const { csrftoken, formUuid, tinymceUrl, formHistoryUrl } = formCreationFormNode.dataset;

        ReactModal.setAppElement(formCreationFormNode);

        ReactDOM.render(
            <IntlProvider messages={messages} locale={locale} defaultLocale="en">
                <TinyMceContext.Provider value={tinymceUrl}>
                    <FormCreationForm csrftoken={csrftoken} formUuid={formUuid} formHistoryUrl={formHistoryUrl} />
                </TinyMceContext.Provider>
            </IntlProvider>,
            formCreationFormNode
        );
    }
};

const mountFormVersions = (locale, messages) => {
    const formVersionsNodes = document.getElementsByClassName('react-form-versions-table');
    if (!formVersionsNodes.length) return;

    for (const formVersionsNode of formVersionsNodes) {
        const { formUuid, csrftoken } = formVersionsNode.dataset;

        ReactDOM.render(
            <IntlProvider messages={messages} locale={locale} defaultLocale="en">
                <FormVersionsTable csrftoken={csrftoken} formUuid={formUuid} />
            </IntlProvider>,
            formVersionsNode
        );
    }
};


const mountDebugComponent = () => {
    const node = document.getElementById('react');
    if (!node) return;
    ReactDOM.render(<Debug />, node);
};


const bootstrapApplication = async () => {
    const lang = document.querySelector('html').getAttribute("lang");
    const messages = await loadLocaleData(lang);

    mountForm(lang, messages);
    mountFormVersions(lang, messages);
};

bootstrapApplication();
mountDebugComponent();
