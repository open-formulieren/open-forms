import React from 'react';
import {createRoot} from 'react-dom/client';
import ReactModal from 'react-modal';

import AppWrapper, {getWrapperProps} from './AppWrapper';
import SessionStatus from './SessionStatus';
import './design_token_values';
import setE2EMarker from './e2e-marker';
import './form-category';
import {TinyMceContext} from './form_design/Context';
import {FormCreationForm} from './form_design/form-creation-form';
import FormVersionsTable from './form_versions/FormVersionsTable';
import './login';
import './plugin_configuration';

const mountForm = wrapperProps => {
  const formCreationFormNodes = document.getElementsByClassName('react-form-create');
  if (!formCreationFormNodes.length) return;

  for (const formCreationFormNode of formCreationFormNodes) {
    const {csrftoken, formUuid, formUrl, tinymceUrl, formHistoryUrl, outgoingRequestsUrl} =
      formCreationFormNode.dataset;

    ReactModal.setAppElement(formCreationFormNode);
    const root = createRoot(formCreationFormNode);

    root.render(
      // Immer updates crash when using strict mode due to mutations being made by formio (?).
      // Strict mode is likely only viable once we've simplified the code substantially.
      <AppWrapper {...wrapperProps} csrftoken={csrftoken} strict={false}>
        <TinyMceContext.Provider value={tinymceUrl}>
          <FormCreationForm
            formUuid={formUuid}
            formUrl={formUrl}
            formHistoryUrl={formHistoryUrl}
            outgoingRequestsUrl={outgoingRequestsUrl}
          />
        </TinyMceContext.Provider>
      </AppWrapper>
    );
  }
};

const mountFormVersions = wrapperProps => {
  const formVersionsNodes = document.getElementsByClassName('react-form-versions-table');
  if (!formVersionsNodes.length) return;

  for (const formVersionsNode of formVersionsNodes) {
    const {formUuid, csrftoken, currentRelease} = formVersionsNode.dataset;
    const root = createRoot(formVersionsNode);

    root.render(
      <AppWrapper {...wrapperProps} csrftoken={csrftoken}>
        <FormVersionsTable formUuid={formUuid} currentRelease={currentRelease} />
      </AppWrapper>
    );
  }
};

const mountSessionStatus = wrapperProps => {
  const nodes = document.querySelectorAll('.react-session-status');
  for (const node of nodes) {
    const root = createRoot(node);
    root.render(
      <AppWrapper {...wrapperProps}>
        <SessionStatus />
      </AppWrapper>
    );
  }
};

const bootstrapApplication = async () => {
  const wrapperProps = await getWrapperProps();
  mountSessionStatus(wrapperProps);
  mountForm(wrapperProps);
  mountFormVersions(wrapperProps);
};

bootstrapApplication();

// this must be the last call in the script, as we rely on the marker being absent
// to detect crashes in the JS via E2E integration tests
setE2EMarker();
