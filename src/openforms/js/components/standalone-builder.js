import {createRoot} from 'react-dom/client';
import ReactModal from 'react-modal';

import AppWrapper, {getWrapperProps} from 'components/admin/AppWrapper';
import {FormContext} from 'components/admin/form_design/Context';
import FormBuilder from 'components/admin/form_design/FormBuilder';
import {onLoaded} from 'utils/dom';

onLoaded(async () => {
  const nodes = document.querySelectorAll('.form-builder');
  if (!nodes.length) return;

  const main = document.getElementById('content-main');
  ReactModal.setAppElement(nodes);

  const wrapperProps = await getWrapperProps();

  for (const node of nodes) {
    const formType = node.dataset.formType ?? 'regular';
    const configurationInput = node.querySelector('.form-builder__configuration-input');
    const components = (JSON.parse(configurationInput.value) || {}).components ?? [];

    const onChange = newConfiguration => {
      configurationInput.value = JSON.stringify(newConfiguration);
    };

    const root = createRoot(node.querySelector('.form-builder__container'));
    root.render(
      <AppWrapper {...wrapperProps}>
        {/* Set up mock context for the standalone editors */}
        <FormContext.Provider
          value={{
            form: {url: '', uuid: '', type: formType},
            components: {},
            formSteps: [],
            formDefinitions: [],
            reusableFormDefinitionsLoaded: true,
            formVariables: [],
            staticVariables: [],
            registrationPluginsVariables: [],
            registrationBackends: [],
            plugins: {},
            languages: [],
            translationEnabled: false,
            updateComponents: () => {},
          }}
        >
          <FormBuilder
            initialComponents={components}
            onChange={newConfiguration => onChange(newConfiguration)}
          />
        </FormContext.Provider>
      </AppWrapper>
    );
  }
});
