import {Form, Formik, useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useEffect} from 'react';
import {FormattedMessage, defineMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {
  DMN_DECISION_DEFINITIONS_LIST,
  DMN_DECISION_DEFINITIONS_VERSIONS_LIST,
} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Select from 'components/admin/forms/Select';
import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';
import ErrorBoundary from 'components/errors/ErrorBoundary';
import {get} from 'utils/fetch';

import {ActionConfigError} from '../types';
import DMNParametersForm from './DMNParametersForm';
import {inputValuesType} from './types';

const ERRORS = {
  required: defineMessage({
    description: 'Required error message',
    defaultMessage: 'This field is required.',
  }),
};

const DecisionDefinitionIdField = () => {
  const {
    values: {pluginId},
    setFieldValue,
    getFieldProps,
    errors,
    touched,
    setFieldTouched,
    handleChange,
  } = useFormikContext();
  const [field] = useField('decisionDefinitionId');

  const {error, value: decisionDefinitions = []} = useAsync(async () => {
    if (!pluginId) return [];

    const response = await get(DMN_DECISION_DEFINITIONS_LIST, {
      engine: pluginId,
    });

    return response.data.map(item => [item.id, item.label]);
  }, [pluginId]);

  useEffect(() => {
    if (!touched.pluginId) return;

    if (!pluginId) {
      setFieldValue('decisionDefinitionId', '');
      return;
    }

    // If pluginId has changed, reset the value of the definition
    setFieldValue('decisionDefinitionId', '');
  }, [pluginId, setFieldValue]);

  if (error) throw error;

  return (
    <Field
      name="decisionDefinitionId"
      htmlFor="decisionDefinitionId"
      label={
        <FormattedMessage
          defaultMessage="Decision definition ID"
          description="Decision definition ID label"
        />
      }
      errors={
        touched.decisionDefinitionId && errors.decisionDefinitionId
          ? [ERRORS[errors.decisionDefinitionId]]
          : []
      }
    >
      <Select
        allowBlank
        choices={decisionDefinitions}
        {...field}
        {...getFieldProps('decisionDefinitionId')}
        onChange={(...args) => {
          // Otherwise the field is set as 'touched' only on the blur event
          setFieldTouched('decisionDefinitionId');
          // If decisionDefinitionId has changed, reset the input/output mappings
          setFieldValue('inputMapping', []);
          setFieldValue('outputMapping', []);
          handleChange(...args);
        }}
      />
    </Field>
  );
};

const DecisionDefinitionVersionField = () => {
  const {
    values: {pluginId, decisionDefinitionId},
    setFieldValue,
    getFieldProps,
    touched,
    setFieldTouched,
    handleChange,
  } = useFormikContext();
  const [field] = useField('decisionDefinitionVersion');

  const {error, value: decisionDefinitionVersions = []} = useAsync(async () => {
    if (!pluginId || !decisionDefinitionId) return [];

    const response = await get(DMN_DECISION_DEFINITIONS_VERSIONS_LIST, {
      engine: pluginId,
      definition: decisionDefinitionId,
    });

    return response.data.map(item => [item.id, item.label]);
  }, [pluginId, decisionDefinitionId]);

  useEffect(() => {
    if (!touched.pluginId && !touched.decisionDefinitionId) return;

    if (!pluginId || !decisionDefinitionId) {
      setFieldValue('decisionDefinitionVersion', '');
      return;
    }

    // If decisionDefinitionId has changed, reset the value of the definition version
    setFieldValue('decisionDefinitionVersion', '');
  }, [pluginId, decisionDefinitionId, setFieldValue]);

  if (error) throw error;

  return (
    <Field
      name="decisionDefinitionVersion"
      htmlFor="decisionDefinitionVersion"
      label={
        <FormattedMessage
          defaultMessage="Decision definition version"
          description="Decision definition version label"
        />
      }
      helpText={
        <FormattedMessage
          description="DMN action: definition version field help text"
          defaultMessage="If left blank, then the most recent version is used."
        />
      }
    >
      <Select
        allowBlank
        choices={decisionDefinitionVersions}
        {...field}
        {...getFieldProps('decisionDefinitionVersion')}
        onChange={(...args) => {
          // Otherwise the field is set as 'touched' only on the blur event
          setFieldTouched('decisionDefinitionVersion');
          handleChange(...args);
        }}
      />
    </Field>
  );
};

const DMNActionConfig = ({initialValues, onSave, errors = {}}) => {
  const {plugins} = useContext(FormContext);

  const validate = values => {
    const errors = {};

    if (values.pluginId === '') {
      errors.pluginId = 'required';
    }

    if (values.decisionDefinitionId === '') {
      errors.decisionDefinitionId = 'required';
    }

    return errors;
  };

  return (
    <ValidationErrorsProvider errors={Object.entries(errors)}>
      <div className="dmn-action-config">
        <Formik
          initialValues={{
            ...initialValues,
            pluginId:
              plugins.availableDMNPlugins.length === 1
                ? plugins.availableDMNPlugins[0].id
                : initialValues.pluginId,
          }}
          onSubmit={values => onSave(values)}
          validate={validate}
        >
          {formik => (
            <Form>
              <fieldset className="aligned">
                <div className="form-row form-row--display-block form-row--no-bottom-line">
                  <Field
                    name="pluginId"
                    htmlFor="pluginId"
                    label={
                      <FormattedMessage defaultMessage="Plugin ID" description="Plugin ID label" />
                    }
                    errors={
                      formik.touched.pluginId && formik.errors.pluginId
                        ? [ERRORS[formik.errors.pluginId]]
                        : []
                    }
                  >
                    <Select
                      id="pluginId"
                      name="pluginId"
                      allowBlank={true}
                      choices={plugins.availableDMNPlugins.map(choice => [choice.id, choice.label])}
                      {...formik.getFieldProps('pluginId')}
                      onChange={(...args) => {
                        // Otherwise the field is set as 'touched' only on the blur event
                        formik.setFieldTouched('pluginId');
                        formik.handleChange(...args);
                      }}
                    />
                  </Field>
                </div>
              </fieldset>

              <ErrorBoundary
                errorMessage={
                  <FormattedMessage
                    description="Admin error for API error when configuring Camunda actions"
                    defaultMessage="Could not retrieve the decision definitions IDs/versions. Is the selected DMN plugin running and properly configured?"
                  />
                }
              >
                <fieldset className="aligned">
                  <div className="form-row form-row--display-block form-row--no-bottom-line">
                    <DecisionDefinitionIdField />
                  </div>
                  <div className="form-row form-row--display-block">
                    <DecisionDefinitionVersionField />
                  </div>
                </fieldset>

                <DMNParametersForm />
              </ErrorBoundary>
              <div className="submit-row">
                <input type="submit" name="_save" value="Save" />
              </div>
            </Form>
          )}
        </Formik>
      </div>
    </ValidationErrorsProvider>
  );
};

DMNActionConfig.propTypes = {
  initialValues: inputValuesType,
  onSave: PropTypes.func.isRequired,
  errors: ActionConfigError,
};

export default DMNActionConfig;
