import {Formik} from 'formik';
import PropTypes from 'prop-types';
import {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {BACKEND_OPTIONS_FORMS} from 'components/admin/form_design/registrations';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import {SubmitAction} from 'components/admin/forms/ActionButton';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {EditIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';
import ErrorBoundary from 'components/errors/ErrorBoundary';

/**
 *
 * @param {Object} p
 * @param {string} p.name - The name of the current registration backend
 * @param {Object} p.variable - The current variable
 * @param {Object} p.component - Empty if there's no matching component, or either the
 *   component that the variable is for, or a child component of an edit grid
 *   variable/component.
 * @param {Object} p.backend - The current backend
 * @param {JSX.Element} p.registrationSummary - The rendered summary of the registration backend for the current variable
 * @param {JSX.Element} p.variableConfigurationEditor - The rendered configuration editor for the current variable
 * @param {(_: Object) => void} p.onChange - The base onChange function to update the base state
 * @returns {JSX.Element} - The rendered summary, containing the backend name, summary and edit icon
 */
const RegistrationSummary = ({
  name,
  variable,
  component = undefined,
  backend,
  registrationSummary,
  variableConfigurationEditor,
  optionsToFormikValues = opts => opts,
  formikValuesToOptions = values => values,
  onChange,
}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const formContext = useContext(FormContext);
  // always pick the right index of the backend from the updated context
  const backendIndex = formContext.registrationBackends.findIndex(item => item.key === backend.key);

  const isForDifferentComponent = component && component.key !== variable.key;

  return (
    <>
      <div style={{display: 'flex', justifyContent: 'space-between'}}>
        <div style={{overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis'}}>
          <span>{name}</span>
        </div>
        <span>
          <EditIcon
            label={intl.formatMessage({
              defaultMessage: 'Edit variable registration',
              description: "'Edit variable registration' icon label",
            })}
            onClick={() => setModalOpen(!modalOpen)}
          />
        </span>
      </div>
      {!isForDifferentComponent && <div>{registrationSummary}</div>}
      <FormModal
        title={
          <FormattedMessage
            description="Variable registration configuration modal title"
            defaultMessage="{varName}: registration configuration for {backendName}"
            values={{
              varName: isForDifferentComponent ? component.label || component.key : variable.name,
              backendName: name,
            }}
          />
        }
        isOpen={modalOpen}
        closeModal={() => setModalOpen(false)}
      >
        <ErrorBoundary
          errorMessage={intl.formatMessage({
            description: 'Registration summary error message',
            defaultMessage: 'Something went wrong while rendering the registration options',
          })}
        >
          <Formik
            initialValues={optionsToFormikValues(backend.options)}
            onSubmit={(values, actions) => {
              const updatedBackend = {...backend, options: formikValuesToOptions(values)};
              onChange({
                target: {name: `form.registrationBackends.${backendIndex}`, value: updatedBackend},
              });
              actions.setSubmitting(false);
              setModalOpen(false);
            }}
          >
            {({handleSubmit}) => (
              <>
                {variableConfigurationEditor}
                <SubmitRow>
                  <SubmitAction
                    onClick={event => {
                      event.preventDefault();
                      handleSubmit(event);
                    }}
                  />
                </SubmitRow>
              </>
            )}
          </Formik>
        </ErrorBoundary>
      </FormModal>
    </>
  );
};

RegistrationSummary.propTypes = {
  name: PropTypes.string.isRequired,
  variable: PropTypes.object.isRequired,
  backend: PropTypes.object.isRequired,
  registrationSummary: PropTypes.element.isRequired,
  variableConfigurationEditor: PropTypes.element.isRequired,
  onChange: PropTypes.func.isRequired,
  optionsToFormikValues: PropTypes.func,
  formikValuesToOptions: PropTypes.func,
};

/**
 * Returns a list of summaries for each registration backend
 *
 * @typedef {{key: string, name: string, options: {[key: string]: any}}} RegistrationBackend
 *
 * @param {Object} p
 * @param {Object} p.variable - The current variable
 * @param {RegistrationBackend[]?} p.registrationBackends - The registration backends to be
 *     taken into account. If not provided, will fallback to the backends from the form context.
 * @returns {JSX.Element} - A <ul> list of summaries
 */
const RegistrationsSummaryList = ({
  variable,
  component = undefined,
  onFieldChange,
  registrationBackends,
}) => {
  const formContext = useContext(FormContext);

  // if we didn't get an explicit component, resolve it from the variable if it's a
  // component variable.
  if (!component && variable.source === VARIABLE_SOURCES.component) {
    component = formContext.components[variable.key];
  }

  /** @type {RegistrationBackend[]} */
  const filteredRegistrationBackends = registrationBackends || formContext.registrationBackends;

  const summaries = [];

  for (const [backendIndex, backend] of filteredRegistrationBackends.entries()) {
    const backendInfo = BACKEND_OPTIONS_FORMS[backend.backend];

    // Check if the registration backend can be configured from the variables tab...
    const configurableFromVariables = backendInfo?.configurableFromVariables;
    if (
      (typeof configurableFromVariables === 'function' &&
        !configurableFromVariables(variable, component, backend.options)) ||
      !configurableFromVariables
    )
      continue;

    // These components are guaranteed to exist if `configurableFromVariables` is true:
    const SummaryHandler = backendInfo.summaryHandler;
    const VariableConfigurationEditor = backendInfo.variableConfigurationEditor;
    summaries.push({
      name: backend.name,
      variable,
      component,
      backend,
      backendIndex,
      registrationSummary: (
        <SummaryHandler
          variable={variable}
          component={component}
          backendOptions={backend.options}
        />
      ),
      variableConfigurationEditor: (
        <VariableConfigurationEditor variable={variable} component={component} />
      ),
      optionsToFormikValues: backendInfo?.optionsToFormikValues,
      formikValuesToOptions: backendInfo?.formikValuesToOptions,
      onChange: onFieldChange,
    });
  }

  if (!summaries.length) {
    return (
      <FormattedMessage
        description="Registration summary no registration backend fallback message"
        defaultMessage="-"
      />
    );
  }

  return (
    <>
      <ul>
        {summaries.map(summary => (
          <li key={`backend-${summary.backendIndex}`}>
            <RegistrationSummary {...summary} />
          </li>
        ))}
      </ul>
    </>
  );
};

RegistrationsSummaryList.propTypes = {
  variable: PropTypes.object.isRequired,
  onFieldChange: PropTypes.func.isRequired,
};

export default RegistrationsSummaryList;
