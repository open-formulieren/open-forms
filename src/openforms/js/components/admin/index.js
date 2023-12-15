import React from 'react';
import ReactDOM from 'react-dom';
import {IntlProvider} from 'react-intl';
import ReactModal from 'react-modal';

import jsonScriptToVar from 'utils/json-script';

import SessionStatus from './SessionStatus';
import './design_token_values';
import setE2EMarker from './e2e-marker';
import './form-category';
import {APIContext, FeatureFlagsContext, TinyMceContext} from './form_design/Context';
import {FormCreationForm} from './form_design/form-creation-form';
import FormVersionsTable from './form_versions/FormVersionsTable';
import {getIntlProviderProps} from './i18n';
import './plugin_configuration';
import './submissions/filter';

const mountForm = intlProps => {
  const formCreationFormNodes = document.getElementsByClassName('react-form-create');
  if (!formCreationFormNodes.length) return;

  for (const formCreationFormNode of formCreationFormNodes) {
    const {csrftoken, formUuid, formUrl, tinymceUrl, formHistoryUrl} = formCreationFormNode.dataset;

    const featureFlags = jsonScriptToVar('feature-flags');

    ReactModal.setAppElement(formCreationFormNode);

    ReactDOM.render(
      <IntlProvider {...intlProps}>
        <TinyMceContext.Provider value={tinymceUrl}>
          <FeatureFlagsContext.Provider value={featureFlags}>
            <APIContext.Provider value={{csrftoken}}>
              <FormCreationForm
                formUuid={formUuid}
                formUrl={formUrl}
                formHistoryUrl={formHistoryUrl}
              />
            </APIContext.Provider>
          </FeatureFlagsContext.Provider>
        </TinyMceContext.Provider>
      </IntlProvider>,
      formCreationFormNode
    );
  }
};

const mountFormVersions = intlProps => {
  const formVersionsNodes = document.getElementsByClassName('react-form-versions-table');
  if (!formVersionsNodes.length) return;

  for (const formVersionsNode of formVersionsNodes) {
    const {formUuid, csrftoken, currentRelease} = formVersionsNode.dataset;

    ReactDOM.render(
      <IntlProvider {...intlProps}>
        <APIContext.Provider value={{csrftoken}}>
          <FormVersionsTable formUuid={formUuid} currentRelease={currentRelease} />
        </APIContext.Provider>
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

const mountSessionStatus = intlProps => {
  const nodes = document.querySelectorAll('.react-session-status');
  for (const node of nodes) {
    ReactDOM.render(
      <IntlProvider {...intlProps}>
        <SessionStatus />
      </IntlProvider>,
      node
    );
  }
};

const bootstrapApplication = async () => {
  const intlProviderProps = await getIntlProviderProps();
  mountSessionStatus(intlProviderProps);
  mountForm(intlProviderProps);
  mountFormVersions(intlProviderProps);
};

bootstrapApplication();

// this must be the last call in the script, as we rely on the marker being absent
// to detect crashes in the JS via E2E integration tests
setE2EMarker();
