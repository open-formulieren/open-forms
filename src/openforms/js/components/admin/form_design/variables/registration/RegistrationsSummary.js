import React from 'react';
import {useIntl} from 'react-intl';

import FAIcon from 'components/admin/FAIcon';
import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';

const RegistrationSummary = ({name, registrationPath}) => {
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
      {registrationPath != null && <div>{registrationPath}</div>}
    </>
  );
};

const RegistrationsSummary = ({variableKey, registrationBackends}) => {
  const summaries = [];

  for (const backend of registrationBackends) {
    const SummaryHandler = BACKEND_OPTIONS_FORMS[backend.key].summaryHandler;
    if (SummaryHandler) {
      summaries.push({
        name: backend.name,
        registrationPath: (
          <SummaryHandler variableKey={variableKey} backendOptions={backend.options} />
        ),
      });
    }
  }

  return (
    <ul>
      {summaries.map(summary => (
        <li>
          <RegistrationSummary {...summary} />
        </li>
      ))}
    </ul>
  );
};

export default RegistrationsSummary;
