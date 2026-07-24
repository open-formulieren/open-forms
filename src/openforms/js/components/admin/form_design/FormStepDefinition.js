import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import MessageList from 'components/admin/MessageList';
import Field, {normalizeErrors} from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import OFFormBuilder from 'components/formio_builder/OFFormBuilder';
import FormIOBuilder from 'components/formio_builder/builder';

import AuthenticationWarning from './AuthenticationWarning';
import ChangedFormDefinitionWarning from './ChangedFormDefinitionWarning';
import {FeatureFlagsContext, FormContext} from './Context';
import LanguageTabs, {DEFAULT_LANGUAGE} from './LanguageTabs';
import LogicWarning from './LogicWarning';
import PluginWarning from './PluginWarning';
import useDetectConfigurationChanged from './useDetectConfigurationChanged';
import useDetectSimpleLogicErrors from './useDetectSimpleLogicErrors';
import {slugify} from './utils';

const emptyConfiguration = {
  display: 'form',
};

/**
 * Load the form builder for a given form definition.
 *
 * Note that the underlying FormIOBuilder creates a ref from the configuration. The
 * actual builder state is maintained by FormioJS itself and we are not driven that
 * state via props - only the initial state!
 *
 * We can solely use the onChange handler to keep track of our own 'application'
 * state to eventually persist the data. This goes against React's best practices,
 * but we're fighting the library at this point.
 *
 */
const FormStepDefinition = ({
  url = '',
  generatedId = '',
  internalName = '',
  index = null,
  slug = '',
  isApplicable = true,
  loginRequired = false,
  isReusable = false,
  translations = {},
  configuration = emptyConfiguration,
  onChange,
  onComponentMutated,
  onFieldChange,
  errors,
  ...props
}) => {
  const intl = useIntl();
  const {
    formSteps,
    registrationBackends,
    form: {type},
  } = useContext(FormContext);
  const featureFlags = useContext(FeatureFlagsContext);

  const isSingleStep = type === 'single_step';

  const setSlug = langCode => {
    // do nothing if there's already a slug set
    if (slug) return;
    // the slug is not translated, and based on the default language. Do nothing if
    // we're not editing the targetting language.
    if (langCode !== DEFAULT_LANGUAGE) return;

    // sort-of taken from Django's jquery prepopulate module
    const name = translations[langCode].name;
    onFieldChange({
      target: {
        name: 'slug',
        value: slugify(name),
      },
    });
  };

  // A 'total configuration': merging all the configurations from the different steps, so that we can figure out if
  // a key is unique across steps
  const componentNamespace = formSteps.map(step => step.configuration?.components || []).flat(1);

  const {changed, affectedForms} = useDetectConfigurationChanged(url, configuration);
  const {warnings} = useDetectSimpleLogicErrors(configuration);
  let componentMessages = errors.reduce((accumulator, [path, message]) => {
    if (!path.startsWith('configuration.componentErrors')) return accumulator;
    accumulator.push({level: 'error', message});
    return accumulator;
  }, []);

  const duplicatedKeys = getDuplicatedComponents(componentNamespace)
    .filter(component =>
      configuration.components.some(configComponent => configComponent.key === component.key)
    )
    .map(component => {
      const componentLocations = getComponentLocations(formSteps, component.key);
      const stepNames = componentLocations.map(step => `"${step.name}"`);
      const numSteps = stepNames.length;
      const tail = stepNames.pop();
      const lead = stepNames.join(', ');
      return intl.formatMessage(
        {
          description: 'Description of which key is duplicated in which steps.',
          defaultMessage: `
            <code>{componentKey}</code>: in
            {numSteps, plural,
              =1 {{tail}}
              other {{lead} and {tail}}
            }
          `,
        },
        {
          code: bits => <code>{bits}</code>,
          componentKey: component.key,
          numSteps,
          lead,
          tail,
        }
      );
    });

  if (duplicatedKeys.length > 0 && errors.length === 0)
    componentMessages.push({
      level: 'warning',
      message: (
        <FormattedMessage
          description="Warning message for duplicated keys"
          defaultMessage={`{numDuplicated, plural,
            =1 {A key is duplicated:}
            other {{numDuplicated} keys are duplicated:}
          } <duplicatedKeys></duplicatedKeys>`}
          values={{
            numDuplicated: duplicatedKeys.length,
            duplicatedKeys: () => (
              <ul>
                {duplicatedKeys.map((msg, index) => (
                  <li key={index}>{msg}</li>
                ))}
              </ul>
            ),
          }}
        />
      ),
    });

  const erroredLanguages = new Set();
  for (const [errPath] of errors) {
    if (!errPath.startsWith('translations.')) continue;
    const [, langCode] = errPath.split('.');
    erroredLanguages.add(langCode);
  }

  const hasName = !!translations[DEFAULT_LANGUAGE].name;

  return (
    <>
      <ChangedFormDefinitionWarning changed={changed} affectedForms={affectedForms} />
      <PluginWarning loginRequired={loginRequired} configuration={configuration} />
      <AuthenticationWarning loginRequired={loginRequired} configuration={configuration} />
      <LogicWarning warnings={warnings} />

      <Fieldset
        title={
          <FormattedMessage
            description="Form definition module title"
            defaultMessage="{isReusable, select, true {Reusable step} other {Step}} settings"
            values={{isReusable: isReusable}}
          />
        }
        collapsible
        initialCollapsed={hasName && slug !== '' && !errors.length}
      >
        <LanguageTabs haveErrors={[...erroredLanguages]}>
          {(langCode, defaultLang) => (
            <>
              <FormRow>
                <Field
                  name={`translations.${langCode}.name`}
                  label={
                    <FormattedMessage
                      defaultMessage="Step name"
                      description="Form step name label"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="Name of the form definition used in this form step"
                      description="Form step name field help text"
                    />
                  }
                  required
                >
                  <TextInput
                    value={translations[langCode].name}
                    onChange={onFieldChange}
                    onBlur={() => setSlug(langCode)}
                  />
                </Field>
              </FormRow>
              <FormRow>
                <Field
                  name="internalName"
                  label={
                    <FormattedMessage
                      defaultMessage="Internal step name"
                      description="Form step internal name label"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="Internal name of the form definition used in this form step"
                      description="Form step internal name field help text"
                    />
                  }
                  disabled={langCode !== defaultLang}
                >
                  <TextInput value={internalName} onChange={onFieldChange} />
                </Field>
              </FormRow>
              <FormRow>
                <Field
                  name="slug"
                  label={
                    <FormattedMessage
                      defaultMessage="Step slug"
                      description="Form step slug label"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="Slug of the form definition used in this form step"
                      description="Form step slug field help text"
                    />
                  }
                  required
                  disabled={langCode !== defaultLang}
                >
                  <TextInput value={slug} onChange={onFieldChange} />
                </Field>
              </FormRow>
              {isSingleStep ? (
                <FormRow>
                  <Field
                    name={`translations.${langCode}.nextText`}
                    label={
                      <FormattedMessage
                        defaultMessage="Next text"
                        description="Form step next text label"
                      />
                    }
                    helpText={
                      <FormattedMessage
                        defaultMessage="The text that will be displayed in the form step to go to the next step. Leave blank to get value from global configuration."
                        description="Form step next text field help text"
                      />
                    }
                  >
                    <TextInput
                      value={translations[langCode].nextText}
                      onChange={onFieldChange}
                      maxLength="50"
                    />
                  </Field>
                </FormRow>
              ) : (
                <>
                  <FormRow>
                    <Field
                      name={`translations.${langCode}.previousText`}
                      label={
                        <FormattedMessage
                          defaultMessage="Previous text"
                          description="Form step previous text label"
                        />
                      }
                      helpText={
                        <FormattedMessage
                          defaultMessage="The text that will be displayed in the form step to go to the previous step. Leave blank to get value from global configuration."
                          description="Form step previous text field help text"
                        />
                      }
                    >
                      <TextInput
                        value={translations[langCode].previousText}
                        onChange={onFieldChange}
                        maxLength="50"
                      />
                    </Field>
                  </FormRow>
                  <FormRow>
                    <Field
                      name={`translations.${langCode}.saveText`}
                      label={
                        <FormattedMessage
                          defaultMessage="Save text"
                          description="Form step save text label"
                        />
                      }
                      helpText={
                        <FormattedMessage
                          defaultMessage="The text that will be displayed in the form step to save the current information. Leave blank to get value from global configuration."
                          description="Form step save text field help text"
                        />
                      }
                    >
                      <TextInput
                        value={translations[langCode].saveText}
                        onChange={onFieldChange}
                        maxLength="50"
                      />
                    </Field>
                  </FormRow>
                </>
              )}
              <FormRow>
                <Field
                  name="isApplicable"
                  errorClassPrefix={'checkbox'}
                  errorClassModifier={'no-padding'}
                >
                  <Checkbox
                    label={
                      <FormattedMessage
                        defaultMessage="Is applicable?"
                        description="Form step is applicable label"
                      />
                    }
                    name="isApplicable"
                    checked={isApplicable}
                    onChange={e =>
                      onFieldChange({target: {name: 'isApplicable', value: !isApplicable}})
                    }
                    disabled={index === 0 || langCode !== defaultLang} // First step can't be n/a by default
                  />
                </Field>
              </FormRow>
              {!isSingleStep && (
                <FormRow>
                  <Field
                    name="loginRequired"
                    errorClassPrefix={'checkbox'}
                    errorClassModifier={'no-padding'}
                  >
                    <Checkbox
                      label={
                        <FormattedMessage
                          defaultMessage="Login required?"
                          description="Form step login required label"
                        />
                      }
                      name="loginRequired"
                      checked={loginRequired}
                      onChange={e =>
                        onFieldChange({target: {name: 'loginRequired', value: !loginRequired}})
                      }
                      disabled={langCode !== defaultLang}
                    />
                  </Field>
                </FormRow>
              )}
              <FormRow>
                <Field
                  name="isReusable"
                  errorClassPrefix={'checkbox'}
                  errorClassModifier={'no-padding'}
                >
                  <Checkbox
                    label={
                      <FormattedMessage
                        defaultMessage="Is reusable?"
                        description="Form step is reusable label"
                      />
                    }
                    name="isReusable"
                    checked={isReusable}
                    onChange={e =>
                      onFieldChange({target: {name: 'isReusable', value: !isReusable}})
                    }
                    disabled={langCode !== defaultLang}
                  />
                </Field>
              </FormRow>
            </>
          )}
        </LanguageTabs>
      </Fieldset>

      <h2>
        <FormattedMessage
          description="Form definition formio configuration"
          defaultMessage="Fields"
        />
      </h2>

      <div className="formio-builder-wrapper">
        <ConfigurationErrors errors={errors} />
        <MessageList messages={componentMessages} />
        {featureFlags.USE_OF_FORM_DESIGNER ? (
          <OFFormBuilder
            configuration={configuration}
            onChange={onChange}
            onComponentMutated={onComponentMutated.bind(null, url || generatedId)}
            componentNamespace={componentNamespace}
            formDefinitionIdentifier={url || generatedId}
          />
        ) : (
          <FormIOBuilder
            configuration={configuration}
            onChange={onChange}
            onComponentMutated={onComponentMutated.bind(null, url || generatedId)}
            componentNamespace={componentNamespace}
            registrationBackendInfo={registrationBackends}
            {...props}
          />
        )}
      </div>
    </>
  );
};

FormStepDefinition.propTypes = {
  configuration: PropTypes.object,
  internalName: PropTypes.string,
  url: PropTypes.string,
  slug: PropTypes.string,
  loginRequired: PropTypes.bool,
  isReusable: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  onComponentMutated: PropTypes.func.isRequired,
  onFieldChange: PropTypes.func.isRequired,
  errors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
  translations: PropTypes.objectOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      saveText: PropTypes.string.isRequired,
      previousText: PropTypes.string.isRequired,
      nextText: PropTypes.string.isRequired,
    })
  ),
};

const ConfigurationErrors = ({errors = []}) => {
  const configurationErrors = errors.filter(
    ([name, err]) => name === 'configuration' || name === 'formDefinition'
  );
  const [hasConfigurationErrors, formattedConfigurationErrors] =
    normalizeErrors(configurationErrors);
  if (!hasConfigurationErrors) return null;
  const errorMessages = formattedConfigurationErrors.map(msg => ({level: 'error', message: msg}));
  return <MessageList messages={errorMessages} />;
};

ConfigurationErrors.propTypes = {
  errors: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
};

const getDuplicatedComponents = componentNameSpace => {
  const allKeys = new Set();
  const duplicates = [];
  componentNameSpace.forEach(component => {
    const {key} = component;
    const keySeen = allKeys.has(key);
    allKeys.add(key);
    if (keySeen && !duplicates.some(duplicate => duplicate.key === component.key))
      duplicates.push(component);
  });

  return duplicates;
};

const getComponentLocations = (formSteps, key) => {
  return formSteps
    .filter(step => step.configuration.components)
    .map(step => {
      if (step.configuration.components.some(component => key == component.key)) return step;
    })
    .filter(Boolean);
};

export default FormStepDefinition;
