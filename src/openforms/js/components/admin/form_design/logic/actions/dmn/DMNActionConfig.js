import {Field, Form, Formik, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {
  DMN_DECISION_DEFINITIONS_LIST,
  DMN_DECISION_DEFINITIONS_VERSIONS_LIST,
} from 'components/admin/form_design/constants';
import {get} from 'utils/fetch';

import VariableMapping from './VariableMapping';
import {EMPTY_OPTION} from './constants';
import {inputValuesType} from './types';

const DecisionDefinitionIdField = () => {
  const {values, setFieldValue} = useFormikContext();
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
    <>
      <label htmlFor="decisionDefinitionId">
        <FormattedMessage
          defaultMessage="Decision definition ID"
          description="Decision definition ID label"
        />
      </label>
      <Field name="decisionDefinitionId" id="decisionDefinitionId" as="select">
        {EMPTY_OPTION}
        {decisionDefinitions.map(choice => (
          <option key={choice[0]} value={choice[0]}>
            {choice[1]}
          </option>
        ))}
      </Field>
    </>
  );
};

const DecisionDefinitionVersionField = () => {
  const {
    values: {pluginId, decisionDefinitionId},
    setFieldValue,
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
    <>
      <label htmlFor="decisionDefinitionVersion">
        <FormattedMessage
          defaultMessage="Decision definition version"
          description="Decision definition version label"
        />
      </label>
      <Field name="decisionDefinitionVersion" id="decisionDefinitionVersion" as="select">
        {EMPTY_OPTION}
        {decisionDefinitionVersions.map(choice => (
          <option key={choice[0]} value={choice[0]}>
            {choice[1]}
          </option>
        ))}
      </Field>
    </>
  );
};

const DMNActionConfig = ({initialValues, onSave}) => {
  const {formVariables, plugins} = useContext(FormContext);

  return (
    <div className="dmn-action-config">
      <Formik initialValues={initialValues} onSubmit={values => onSave(values)}>
        {({values}) => (
          <Form>
            <fieldset className="aligned">
              <div className="form-row">
                <label htmlFor="pluginId">
                  <FormattedMessage defaultMessage="Plugin ID" description="Plugin ID label" />
                </label>
                <Field name="pluginId" id="pluginId" as="select">
                  {plugins.availableDMNPlugins.map(choice => (
                    <option key={choice.id} value={choice.id}>
                      {choice.label}
                    </option>
                  ))}
                  {EMPTY_OPTION}
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
                  values={values}
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
                  values={values}
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
