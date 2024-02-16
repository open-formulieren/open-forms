import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import FAIcon from 'components/admin/FAIcon';
import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';
import ButtonContainer from 'components/admin/forms/ButtonContainer';

/**
 *
 * @param {Object} p
 * @param {string} p.name - The name of the current registration backend
 * @param {JSX.Element} p.registrationSummary - The rendered summary of the registration backend for a specific variable
 * @returns {JSX.Element} - The rendered summary, containing the backend name, summary and edit icon
 */
const RegistrationSummary = ({name, registrationSummary}) => {
  const intl = useIntl();

  return (
    <>
      <span>{name}</span>
      <span>
        <FAIcon
          icon="edit"
          title={intl.formatMessage({
            defaultMessage: 'Edit variable registration',
            description: "'Edit variable registration' icon label",
          })}
          extraClassname="fa-lg actions__action"
          onClick={() => {}}
        />
      </span>
      <div>{registrationSummary}</div>
    </>
  );
};

/**
 * Returns a list of summaries for each registration backend
 *
 * @typedef {{key: string, name: string, options: {[key: string]: any}}} RegistrationBackend
 *
 * @param {Object} p
 * @param {string} p.variableKey - The current variable
 * @param {RegistrationBackend[]} p.registrationBackends - The form's registration backends
 * @returns {JSX.Element} - A <ul> list of summaries
 */
const RegistrationsSummary = ({variableKey, registrationBackends}) => {
  const summaries = [];
  let canConfigureBackend = false;

  for (const backend of registrationBackends) {
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
    const formVariableConfigured = backendInfo.formVariableConfigured(variableKey, backend.options);
    if (formVariableConfigured) {
      // a summary handler is guaranteed to exist if `configurableFromVariables` is true:
      const SummaryHandler = BACKEND_OPTIONS_FORMS[backend.key].summaryHandler;
      const registrationSummary = (
        <SummaryHandler variableKey={variableKey} backendOptions={backend.options} />
      );
      summaries.push({
        name: backend.name,
        registrationSummary: registrationSummary,
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
