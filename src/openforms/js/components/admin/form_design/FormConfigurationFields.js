import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, defineMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox, DateTimeInput, TextArea, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {getTranslatedChoices} from 'utils/i18n';

import AuthPluginAutoLoginField from './AuthPluginAutoLoginField';
import AuthPluginField from './AuthPluginField';
import AuthPluginOptions from './AuthPluginOptions';
import TYPES from './types';

const SUMBISSION_ALLOWED_CHOICES = [
  [
    'yes',
    defineMessage({
      description: 'option "yes" of "submission_allowed"',
      defaultMessage: 'Yes',
    }),
  ],
  [
    'no_with_overview',
    defineMessage({
      description: 'option "no_with_overview" of "submission_allowed"',
      defaultMessage: 'No (with overview page)',
    }),
  ],
  [
    'no_without_overview',
    defineMessage({
      description: 'option "no_without_overview" of "submission_allowed"',
      defaultMessage: 'No (without overview page)',
    }),
  ],
];

const STATEMENT_CHECKBOX_CHOICES = [
  [
    'global_setting',
    defineMessage({
      description: 'option "global_setting" of statement checkbox configuration',
      defaultMessage: 'Global setting',
    }),
  ],
  [
    'required',
    defineMessage({
      description: 'option "required" of statement checkbox configuration',
      defaultMessage: 'Required',
    }),
  ],
  [
    'disabled',
    defineMessage({
      description: 'option "disabled" of statement checkbox configuration',
      defaultMessage: 'Do not ask',
    }),
  ],
];

const getCategoryChoices = available => {
  const choices = [['', '----']];

  for (let category of available) {
    let label = category.name;
    // join parts like a path
    for (let ancestor of category.ancestors.concat().reverse()) {
      label = ancestor.name + ' / ' + label;
    }
    choices.push([category.url, label]);
  }
  return choices;
};

const getThemeChoices = available => {
  const choices = [['', '----'], ...available.map(theme => [theme.url, theme.name])];
  return choices;
};

const AvailabilityFields = ({active, activateOn, deactivateOn, maintenanceMode, onChange}) => {
  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Form availability fieldset title"
          defaultMessage="Availability {isAvailable, select, true {(status: publicly available)} other {}}"
          values={{
            isAvailable: active && !maintenanceMode,
          }}
        />
      }
      collapsible
      initialCollapsed={active}
    >
      <FormRow>
        <Checkbox
          name="form.active"
          label={<FormattedMessage defaultMessage="Active" description="Form active field label" />}
          helpText={
            <FormattedMessage
              defaultMessage="Whether the form is active or not. Deactivated forms cannot be started."
              description="Form active field help text"
            />
          }
          checked={active}
          onChange={event => onCheckboxChange(event, active)}
        />
      </FormRow>
      <FormRow>
        <Field
          name="form.activateOn"
          label={
            <FormattedMessage
              defaultMessage="Activate on"
              description="Form activation field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="When the form should be activated."
              description="Form activation field help text"
            />
          }
        >
          <DateTimeInput value={activateOn} onChange={onChange} enableTime={true} />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="form.deactivateOn"
          label={
            <FormattedMessage
              defaultMessage="Deactivate on"
              description="Form deactivation field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="When the form should be deactivated."
              description="Form deactivation field help text"
            />
          }
        >
          <DateTimeInput value={deactivateOn} onChange={onChange} enableTime={true} />
        </Field>
      </FormRow>
      <FormRow>
        <Checkbox
          name="form.maintenanceMode"
          label={
            <FormattedMessage
              defaultMessage="Maintenance mode"
              description="Form maintenance mode field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Users will not be able to start the form if it is in maintenance mode."
              description="Form maintenance mode field help text"
            />
          }
          checked={maintenanceMode}
          onChange={event => onCheckboxChange(event, maintenanceMode)}
        />
      </FormRow>
    </Fieldset>
  );
};

AvailabilityFields.propTypes = {
  active: PropTypes.bool.isRequired,
  activateOn: PropTypes.string,
  deactivateOn: PropTypes.string,
  maintenanceMode: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
};

const AuthenticationFields = ({
  availableAuthPlugins,
  selectedAuthPlugins,
  onAuthPluginChange,
  autoLoginAuthenticationBackend,
  onChange,
  authBackends,
}) => {
  const eligibleAutoLoginPlugins = availableAuthPlugins.filter(plugin =>
    selectedAuthPlugins.includes(plugin.id)
  );
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Form authentication fieldset title"
          defaultMessage="Authentication {hasAuth, select, false {(status: none configured)} other {}}"
          values={{
            hasAuth: selectedAuthPlugins.length > 0,
          }}
        />
      }
      collapsible
    >
      <FormRow>
        <AuthPluginField
          availableAuthPlugins={availableAuthPlugins}
          selectedAuthPlugins={selectedAuthPlugins}
          onChange={onAuthPluginChange}
        />
      </FormRow>
      {eligibleAutoLoginPlugins.length ? (
        <FormRow>
          <Field
            name="form.autoLoginAuthenticationBackend"
            label={
              <FormattedMessage
                defaultMessage="Authentication automatic login"
                description="Auto-login field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Select which authentication backend is automatically redirected to."
                description="Auto-login field help text"
              />
            }
          >
            <AuthPluginAutoLoginField
              eligiblePlugins={eligibleAutoLoginPlugins}
              value={autoLoginAuthenticationBackend}
              onChange={onChange}
            />
          </Field>
        </FormRow>
      ) : null}
      {authBackends.map((authBackend, index) => (
        <AuthPluginOptions
          key={authBackend.backend}
          name={`form.authBackends.${index}.options`}
          authBackend={authBackend}
          availableAuthPlugins={availableAuthPlugins}
          onChange={onChange}
        />
      ))}
    </Fieldset>
  );
};

const PresentationFields = ({
  availableThemes,
  theme,
  showProgressIndicator,
  showSummaryProgress,
  onChange,
}) => {
  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };

  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Form presentation fieldset title"
          defaultMessage="Presentation / appearance"
        />
      }
      collapsible
    >
      {availableThemes.length ? (
        <FormRow>
          <Field
            name="form.theme"
            label={<FormattedMessage defaultMessage="Theme" description="Form theme field label" />}
            helpText={
              <FormattedMessage
                defaultMessage="Optional theme to use for styling."
                description="Form theme field help text"
              />
            }
          >
            <Select
              choices={getThemeChoices(availableThemes)}
              value={theme || ''}
              onChange={onChange}
            />
          </Field>
        </FormRow>
      ) : null}
      <FormRow>
        <Checkbox
          name="form.showProgressIndicator"
          label={
            <FormattedMessage
              defaultMessage="Show progress indicator"
              description="Progress indicator field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Whether the step progression should be displayed in the UI or not."
              description="Progress indicator help text"
            />
          }
          checked={showProgressIndicator}
          onChange={event => onCheckboxChange(event, showProgressIndicator)}
        />
      </FormRow>
      <FormRow>
        <Checkbox
          name="form.showSummaryProgress"
          label={
            <FormattedMessage
              defaultMessage="Show summary progress"
              description="showSummaryProgress field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Whether to display the short progress summary, indicating the current step number and total amount of steps."
              description="Summary of the progress help text"
            />
          }
          checked={showSummaryProgress}
          onChange={event => onCheckboxChange(event, showSummaryProgress)}
        />
      </FormRow>
    </Fieldset>
  );
};

const SubmissionFields = ({
  isAppointment,
  submissionAllowed,
  askPrivacyConsent,
  askStatementOfTruth,
  onChange,
}) => {
  const intl = useIntl();
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Form submission settings fieldset title"
          defaultMessage="Submission settings"
        />
      }
      collapsible
    >
      <div className="description">
        <FormattedMessage
          description="Form submission settings description"
          defaultMessage={`The configuration options here control if the user can submit
          the form on the overview page and what the requirements are to do so.`}
        />
      </div>
      {!isAppointment && (
        <FormRow>
          <Field
            name="form.submissionAllowed"
            label={
              <FormattedMessage
                defaultMessage="Submission allowed"
                description="Form submissionAllowed field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Whether the user is allowed to submit this form or not, and whether the overview page should be shown if they are not."
                description="Form submissionAllowed field help text"
              />
            }
          >
            <Select
              choices={getTranslatedChoices(intl, SUMBISSION_ALLOWED_CHOICES)}
              value={submissionAllowed}
              onChange={onChange}
            />
          </Field>
        </FormRow>
      )}
      <FormRow>
        <Field
          name="form.askPrivacyConsent"
          label={
            <FormattedMessage
              defaultMessage="Ask privacy consent"
              description="Form askPrivacyConsent field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="If enabled, the user will have to agree to the privacy policy before submitting a form."
              description="Form askPrivacyConsent field help text"
            />
          }
        >
          <Select
            choices={getTranslatedChoices(intl, STATEMENT_CHECKBOX_CHOICES)}
            value={askPrivacyConsent}
            onChange={onChange}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="form.askStatementOfTruth"
          label={
            <FormattedMessage
              defaultMessage="Ask statement of truth"
              description="Form askStatementOfTruth field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="If enabled, the user will have to agree that they filled out the form truthfully before submitting it."
              description="Form askStatementOfTruth field help text"
            />
          }
        >
          <Select
            choices={getTranslatedChoices(intl, STATEMENT_CHECKBOX_CHOICES)}
            value={askStatementOfTruth}
            onChange={onChange}
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

const FeatureFields = ({isAppointment, translationEnabled, suspensionAllowed, onChange}) => {
  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };
  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Form feature fields fieldset title"
          defaultMessage="Features"
        />
      }
    >
      <FormRow>
        <Checkbox
          name="form.appointmentOptions.isAppointment"
          label={
            <FormattedMessage
              defaultMessage="Appointment enabled"
              description="Form appointment enabled field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Indicates whether appointments are enabled for this form."
              description="Form appointment enabled field help text"
            />
          }
          checked={isAppointment}
          onChange={event => onCheckboxChange(event, isAppointment)}
        />
      </FormRow>

      <FormRow>
        <Checkbox
          name="form.translationEnabled"
          label={
            <FormattedMessage
              defaultMessage="Translation enabled"
              description="Form translation enabled field label"
            />
          }
          helpText={
            <FormattedMessage
              defaultMessage="Indicates whether translations are enabled for this form."
              description="Form translation enabled field help text"
            />
          }
          checked={translationEnabled}
          onChange={event => onCheckboxChange(event, translationEnabled)}
        />
      </FormRow>

      {!isAppointment && (
        <FormRow>
          <Checkbox
            name="form.suspensionAllowed"
            label={
              <FormattedMessage
                defaultMessage="Suspension allowed"
                description="Form suspensionAllowed field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Whether the user is allowed to suspend this form or not."
                description="Form suspensionAllowed field help text"
              />
            }
            checked={suspensionAllowed}
            onChange={event => onCheckboxChange(event, suspensionAllowed)}
          />
        </FormRow>
      )}
    </Fieldset>
  );
};

/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormConfigurationFields = ({
  form,
  onChange,
  availableAuthPlugins,
  availableThemes,
  selectedAuthPlugins,
  onAuthPluginChange,
  availableCategories,
}) => {
  const {
    uuid,
    internalName,
    internalRemarks,
    slug,
    showProgressIndicator,
    showSummaryProgress,
    active,
    category,
    theme,
    isDeleted,
    activateOn,
    deactivateOn,
    maintenanceMode,
    translationEnabled,
    submissionAllowed,
    suspensionAllowed,
    askPrivacyConsent,
    askStatementOfTruth,
    appointmentOptions,
    newRendererEnabled,
  } = form;

  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };

  const isAppointment = appointmentOptions?.isAppointment ?? false;

  return (
    <>
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Form configuration"
            description="Form configuration fieldset title"
          />
        }
      >
        <FormRow>
          <Field
            name="form.uuid"
            label={<FormattedMessage defaultMessage="ID" description="Form ID field label" />}
            helpText={
              <FormattedMessage
                defaultMessage="Unique identifier for the form"
                description="Form ID field help text"
              />
            }
            required
          >
            <TextInput value={uuid} onChange={onChange} disabled={true} />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name="form.internalName"
            label={
              <FormattedMessage
                defaultMessage="Internal name"
                description="Form name field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Internal name/title of the form"
                description="Form name field help text"
              />
            }
          >
            <TextInput value={internalName} onChange={onChange} maxLength="150" />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name="form.internalRemarks"
            label={
              <FormattedMessage
                defaultMessage="Internal remarks"
                description="Internal form remarks field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage={`
                Remarks or intentions about the form. Can also be used
                to save notes for later use or for another admin user.
                `}
                description="Internal form remarks field help text"
              />
            }
          >
            <TextArea rows={5} cols={85} value={internalRemarks} onChange={onChange} />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name="form.slug"
            label={<FormattedMessage defaultMessage="Slug" description="Form slug field label" />}
            helpText={
              <FormattedMessage
                defaultMessage="Slug of the form, used in URLs"
                description="Form slug field help text"
              />
            }
            required
          >
            <TextInput value={slug} onChange={onChange} />
          </Field>
        </FormRow>

        <FormRow>
          <Field
            name="form.category"
            label={
              <FormattedMessage defaultMessage="Category" description="Form category field label" />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Optional category for internal organisation."
                description="Form category field help text"
              />
            }
          >
            <Select
              choices={getCategoryChoices(availableCategories)}
              value={category || ''}
              onChange={onChange}
            />
          </Field>
        </FormRow>

        <FormRow>
          <Checkbox
            name="form.isDeleted"
            label={
              <FormattedMessage
                defaultMessage="Is deleted"
                description="Form deleted field label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage="Whether the form is (soft) deleted"
                description="Form deleted field help text"
              />
            }
            checked={isDeleted}
            onChange={event => onCheckboxChange(event, isDeleted)}
          />
        </FormRow>
      </Fieldset>

      <FeatureFields
        isAppointment={isAppointment}
        translationEnabled={translationEnabled}
        suspensionAllowed={suspensionAllowed}
        onChange={onChange}
      />

      {!isAppointment && (
        <AuthenticationFields
          availableAuthPlugins={availableAuthPlugins}
          selectedAuthPlugins={selectedAuthPlugins}
          onAuthPluginChange={onAuthPluginChange}
          autoLoginAuthenticationBackend={form.autoLoginAuthenticationBackend}
          onChange={onChange}
          authBackends={form.authBackends}
        />
      )}

      <PresentationFields
        availableThemes={availableThemes}
        theme={theme}
        showProgressIndicator={showProgressIndicator}
        showSummaryProgress={showSummaryProgress}
        onChange={onChange}
      />

      <AvailabilityFields
        active={active}
        activateOn={activateOn}
        deactivateOn={deactivateOn}
        maintenanceMode={maintenanceMode}
        onChange={onChange}
      />

      <SubmissionFields
        isAppointment={isAppointment}
        submissionAllowed={submissionAllowed}
        askPrivacyConsent={askPrivacyConsent}
        askStatementOfTruth={askStatementOfTruth}
        onChange={onChange}
      />

      <Fieldset
        title={
          <FormattedMessage
            description="Form feature flags fieldset title"
            defaultMessage="Experimental features"
          />
        }
        collapsible
        initialCollapsed
      >
        <FormRow>
          <Checkbox
            name="form.newRendererEnabled"
            label={
              <FormattedMessage
                description="New renderer enabled feature flag label"
                defaultMessage="Enable new renderer"
              />
            }
            helpText={
              <FormattedMessage
                description="New renderer enabled feature flag help text"
                defaultMessage={`Enable the EXPERIMENTAL new renderer. Disclaimer: the
                new renderer is not feature complete and is very likely to contain bugs.
                You should not enable this in production.`}
              />
            }
            checked={newRendererEnabled}
            onChange={event => onCheckboxChange(event, newRendererEnabled)}
          />
        </FormRow>
      </Fieldset>
    </>
  );
};

const statementChoices = PropTypes.oneOf(STATEMENT_CHECKBOX_CHOICES.map(opt => opt[0]));

FormConfigurationFields.propTypes = {
  form: PropTypes.shape({
    uuid: PropTypes.string.isRequired,
    internalName: PropTypes.string.isRequired,
    internalRemarks: PropTypes.string.isRequired,
    slug: PropTypes.string.isRequired,
    showProgressIndicator: PropTypes.bool.isRequired,
    showSummaryProgress: PropTypes.bool.isRequired,
    active: PropTypes.bool.isRequired,
    isDeleted: PropTypes.bool.isRequired,
    maintenanceMode: PropTypes.bool.isRequired,
    translationEnabled: PropTypes.bool.isRequired,
    submissionAllowed: PropTypes.oneOf(SUMBISSION_ALLOWED_CHOICES.map(opt => opt[0])),
    suspensionAllowed: PropTypes.bool.isRequired,
    askPrivacyConsent: statementChoices.isRequired,
    askStatementOfTruth: statementChoices.isRequired,
    appointmentOptions: PropTypes.shape({
      isAppointment: PropTypes.bool.isRequired,
    }),
    authBackends: PropTypes.arrayOf(
      PropTypes.shape({
        backend: PropTypes.string.isRequired, // Auth plugin id
        // Options configuration shape is specific to plugin
        options: PropTypes.object,
      })
    ).isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
  availableAuthPlugins: PropTypes.arrayOf(TYPES.AuthPlugin).isRequired,
  selectedAuthPlugins: PropTypes.array.isRequired,
  onAuthPluginChange: PropTypes.func.isRequired,
};

export default FormConfigurationFields;
