import React from 'react';
import ReactDOM from 'react-dom';
import ReactModal from 'react-modal';
import {IntlProvider} from 'react-intl';

import {FormCreationForm} from './form_design/form-creation-form';
import {TinyMceContext, FeatureFlagsContext} from './form_design/Context';
import FormVersionsTable from './form_versions/FormVersionsTable';
import './sdk-snippet';
import './plugin_configuration';
import enableKeyboardShortcuts from "./Keyboard";

import Debug from './debug';
import SessionStatus from './SessionStatus';
import {getIntlProviderProps} from './i18n';
import jsonScriptToVar from '../../utils/json-script';


const mountForm = (intlProps) => {
    const formCreationFormNodes = document.getElementsByClassName('react-form-create');
    if (!formCreationFormNodes.length) return;

    for (const formCreationFormNode of formCreationFormNodes) {
        const { csrftoken, formUuid, tinymceUrl, formHistoryUrl } = formCreationFormNode.dataset;

        const featureFlags = jsonScriptToVar('feature-flags');

        ReactModal.setAppElement(formCreationFormNode);

        ReactDOM.render(
            <IntlProvider {...intlProps}>
                <TinyMceContext.Provider value={tinymceUrl}>
                    <FeatureFlagsContext.Provider value={featureFlags}>
                        <FormCreationForm csrftoken={csrftoken} formUuid={formUuid} formHistoryUrl={formHistoryUrl} />
                    </FeatureFlagsContext.Provider>
                </TinyMceContext.Provider>
            </IntlProvider>,
            formCreationFormNode
        );
    }
};

const mountFormVersions = (intlProps) => {
    const formVersionsNodes = document.getElementsByClassName('react-form-versions-table');
    if (!formVersionsNodes.length) return;

    for (const formVersionsNode of formVersionsNodes) {
        const { formUuid, csrftoken } = formVersionsNode.dataset;

        ReactDOM.render(
            <IntlProvider {...intlProps}>
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


const mountSessionStatus = (intlProps) => {
    const nodes = document.querySelectorAll('.react-session-status');
    for (const node of nodes) {
        ReactDOM.render(
            <IntlProvider {...intlProps}>
                <SessionStatus />
            </IntlProvider>,
            node
        );
    }
}


const bootstrapApplication = async () => {
    const intlProviderProps = await getIntlProviderProps();
    mountSessionStatus(intlProviderProps);
    mountForm(intlProviderProps);
    mountFormVersions(intlProviderProps);
};

bootstrapApplication();
mountDebugComponent();
enableKeyboardShortcuts();
