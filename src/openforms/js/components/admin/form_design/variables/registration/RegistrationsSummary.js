import {produce} from 'immer';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import FAIcon from 'components/admin/FAIcon';
import {FormContext} from 'components/admin/form_design/Context';
import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';
import {SubmitAction} from 'components/admin/forms/ActionButton';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';

/**
 *
 * @param {Object} p
 * @param {string} p.name - The name of the current registration backend
 * @param {Object} p.variable - The current variable
 * @param {Object} p.backend - The current backend
 * @param {number} p.backendIndex - The current backend index (used to update the base state)
 * @param {JSX.Element} p.registrationSummary - The rendered summary of the registration backend for the current variable
 * @param {JSX.Element} p.variableConfigurationEditor - The rendered configuration editor for the current variable
 * @param {() => Object} p.getOptions - The function returing the new backend options. It is provided by the configuration editor
 * @param {(_: Object) => void} p.onChange - The base onChange function to update the base state
 * @returns {JSX.Element} - The rendered summary, containing the backend name, summary and edit icon
 */
const RegistrationSummary = ({
  name,
  variable,
  backend,
  backendIndex,
  registrationSummary,
  variableConfigurationEditor,
  getOptions,
  onChange,
}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);

  const onRegistrationOptionsChange = formData => {
    onChange({target: `form.registrationBackend.${backendIndex}`, value: formData});
  };

  const saveRegistrationOptions = () => {
    const newOptions = getOptions();
    onRegistrationOptionsChange(
      produce(backend, draft => {
        draft.options = newOptions;
      })
    );
  };

  return (
    <>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <div style={{overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis'}}>
          <span>{name}</span>
        </div>
        <span>
          <FAIcon
            icon="edit"
            title={intl.formatMessage({
              defaultMessage: 'Edit variable registration',
              description: "'Edit variable registration' icon label",
            })}
            extraClassname="fa-lg actions__action"
            onClick={() => setModalOpen(!modalOpen)}
          />
        </span>
      </div>
      <div>{registrationSummary}</div>
      <FormModal
        title={`'${variable.name}' registration configuration for '${name}'`}
        isOpen={modalOpen}
        closeModal={() => setModalOpen(false)}
      >
        {variableConfigurationEditor}
        <SubmitRow>
          <SubmitAction
            onClick={event => {
              event.preventDefault();
              saveRegistrationOptions();
              setModalOpen(false);
            }}
          />
        </SubmitRow>
      </FormModal>
    </>
  );
};

/**
 * Returns a list of summaries for each registration backend
 *
 * @typedef {{key: string, name: string, options: {[key: string]: any}}} RegistrationBackend
 *
 * @param {Object} p
 * @param {Object} p.variable - The current variable
 * @returns {JSX.Element} - A <ul> list of summaries
 */
const RegistrationsSummary = ({variable, onFieldChange}) => {
  const formContext = useContext(FormContext);

  /** @type {RegistrationBackend[]} */
  const registrationBackends = formContext.registrationBackends;

  const summaries = [];
  let canConfigureBackend = false;

  for (const [backendIndex, backend] of registrationBackends.entries()) {
    const backendInfo = BACKEND_OPTIONS_FORMS[backend.key];

    // Check if the registration backend can be configured from the variables tab...
    const configurableFromVariables = backendInfo.configurableFromVariables;
    if (
      (typeof configurableFromVariables === 'function' &&
        !configurableFromVariables(backend.options)) ||
      !configurableFromVariables
    )
      continue;

    // ... if it is the case, check if the variable is already configured:
    const formVariableConfigured = backendInfo.formVariableConfigured(variable, backend.options);
    if (formVariableConfigured) {
      // These components are guaranteed to exist if `configurableFromVariables` is true:
      const SummaryHandler = BACKEND_OPTIONS_FORMS[backend.key].summaryHandler;
      const VariableConfigurationEditor =
        BACKEND_OPTIONS_FORMS[backend.key].variableConfigurationEditor;

      const [getOptions, setGetOptions] = useState();

      summaries.push({
        name: backend.name,
        variable,
        backend,
        backendIndex,
        registrationSummary: (
          <SummaryHandler variable={variable} backendOptions={backend.options} />
        ),
        variableConfigurationEditor: (
          <VariableConfigurationEditor
            variable={variable}
            backend={backend}
            setGetOptions={setGetOptions}
          />
        ),
        getOptions,
        onChange: onFieldChange,
      });
    } else {
      canConfigureBackend = true;
    }
  }

  return (
    <>
      <ul>
        {summaries.map(summary => (
          <li>
            <RegistrationSummary {...summary} />
          </li>
        ))}
      </ul>
      {canConfigureBackend && (
        <ButtonContainer>
          <FormattedMessage
            defaultMessage="Add another"
            description="Registrations column 'Add another' label"
          />
        </ButtonContainer>
      )}
    </>
  );
};

export default RegistrationsSummary;
