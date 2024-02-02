import {Form, Formik, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, defineMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {
  DMN_DECISION_DEFINITIONS_LIST,
  DMN_DECISION_DEFINITIONS_VERSIONS_LIST,
} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Select from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

import VariableMapping from './VariableMapping';
import {inputValuesType} from './types';

const ERRORS = {
  required: defineMessage({
    description: 'Required error message',
    defaultMessage: 'This field is required.',
  }),
};

const DecisionDefinitionIdField = () => {
  const {values, setFieldValue, getFieldProps, errors, touched} = useFormikContext();
  const [decisionDefinitions, setDecisionDefinitions] = useState([]);

  useAsync(async () => {
    if (!values.pluginId) {
      setFieldValue('decisionDefinitionId', '');
      setDecisionDefinitions([]);
      return;
    }

    const response = await get(DMN_DECISION_DEFINITIONS_LIST, {
      engine: values.pluginId,
    });

    const definitionChoices = response.data.map(item => [item.id, item.label]);
    setDecisionDefinitions(definitionChoices);

    // If pluginId has changed, reset the value of the definition
    if (
      values.decisionDefinitionId !== '' &&
      !definitionChoices.find(item => item[0] === values.decisionDefinitionId)
    ) {
      setFieldValue('decisionDefinitionId', '');
    }
  }, [values.pluginId, setFieldValue]);

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
        id="decisionDefinitionId"
        name="decisionDefinitionId"
        allowBlank={true}
        choices={decisionDefinitions}
        {...getFieldProps('decisionDefinitionId')}
      />
    </Field>
  );
};

const DecisionDefinitionVersionField = () => {
  const {
    values: {pluginId, decisionDefinitionId},
    setFieldValue,
    getFieldProps,
  } = useFormikContext();
  const [decisionDefinitionVersions, setDecisionDefinitionVersions] = useState([]);

  useAsync(async () => {
    if (!pluginId || !decisionDefinitionId) {
      setFieldValue('decisionDefinitionVersion', '');
      setDecisionDefinitionVersions([]);
      return;
    }

    const response = await get(DMN_DECISION_DEFINITIONS_VERSIONS_LIST, {
      engine: pluginId,
      definition: decisionDefinitionId,
    });

    const versionChoices = response.data.map(item => [item.id, item.label]);
    setDecisionDefinitionVersions(versionChoices);

    // If decisionDefinitionId has changed, reset the value of the definition version if the new decision definition
    // does not have that version
    if (
      values.decisionDefinitionVersion !== '' &&
      !versionChoices.find(item => item[0] === values.decisionDefinitionVersion)
    ) {
      setFieldValue('decisionDefinitionVersion', '');
    }
  }, [pluginId, decisionDefinitionId, setFieldValue]);

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
    >
      <Select
        id="decisionDefinitionVersion"
        name="decisionDefinitionVersion"
        allowBlank={true}
        choices={decisionDefinitionVersions}
        {...getFieldProps('decisionDefinitionVersion')}
      />
    </Field>
  );
};

const DMNActionConfig = ({initialValues, onSave}) => {
  const {formVariables, plugins} = useContext(FormContext);

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
    <div className="dmn-action-config">
      <Formik initialValues={initialValues} onSubmit={values => onSave(values)} validate={validate}>
        {formik => (
          <Form>
            <fieldset className="aligned">
              <div className="form-row">
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
                  />
                </Field>
              </div>
              <div className="form-row">
                <DecisionDefinitionIdField />
              </div>
              <div className="form-row">
                <DecisionDefinitionVersionField />
              </div>
            </fieldset>

            <div className="mappings">
              <div className="form-row">
                <h1>
                  <FormattedMessage
                    defaultMessage="Input mapping"
                    description="Input mapping title"
                  />
                </h1>
                <VariableMapping
                  mappingName="inputMapping"
                  values={formik.values}
                  formVariables={formVariables}
                />
              </div>
              <div className="form-row">
                <h1>
                  <FormattedMessage
                    defaultMessage="Output mapping"
                    description="Output mapping title"
                  />
                </h1>
                <VariableMapping
                  mappingName="outputMapping"
                  values={formik.values}
                  formVariables={formVariables}
                />
              </div>
            </div>

            <div className="submit-row">
              <input type="submit" name="_save" value="Save" />
            </div>
          </Form>
        )}
      </Formik>
    </div>
  );
};

DMNActionConfig.propTypes = {
  initialValues: inputValuesType,
  onSave: PropTypes.func.isRequired,
};

export default DMNActionConfig;
