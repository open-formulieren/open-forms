import {useFormikContext} from 'formik';
import React, {useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {DMN_DECISION_DEFINITIONS_PARAMS_LIST} from 'components/admin/form_design/constants';
import {get} from 'utils/fetch';

import VariableMapping from './VariableMapping';

const EMPTY_DMN_PARAMS = {inputs: [], outputs: []};

const DMNParametersForm = () => {
  const {
    values: {pluginId, decisionDefinitionId, decisionDefinitionVersion},
  } = useFormikContext();
  const {formVariables} = useContext(FormContext);

  const {loading, value: dmnParams = EMPTY_DMN_PARAMS} = useAsync(async () => {
    if (!pluginId || !decisionDefinitionId) {
      return EMPTY_DMN_PARAMS;
    }

    const queryParams = {
      engine: pluginId,
      definition: decisionDefinitionId,
    };

    if (decisionDefinitionVersion) {
      queryParams.version = decisionDefinitionVersion;
    }

    const response = await get(DMN_DECISION_DEFINITIONS_PARAMS_LIST, queryParams);

    return {
      inputs: response.data.inputs.map(inputParam => [inputParam.expression, inputParam.label]),
      outputs: response.data.outputs.map(outputParam => [outputParam.name, outputParam.label]),
    };
  }, [pluginId, decisionDefinitionId, decisionDefinitionVersion]);

  const variablesChoices = formVariables.map(variable => [variable.key, variable.name]);

  return (
    <div className="mappings">
      <div className="mappings__mapping">
        <h3 className="react-modal__title">
          <FormattedMessage defaultMessage="Input mapping" description="Input mapping title" />
        </h3>
        <VariableMapping
          loading={loading}
          mappingName="inputMapping"
          formVariables={variablesChoices}
          dmnVariables={dmnParams.inputs}
        />
      </div>
      <div className="mappings__mapping">
        <h3 className="react-modal__title">
          <FormattedMessage defaultMessage="Output mapping" description="Output mapping title" />
        </h3>
        <VariableMapping
          loading={loading}
          mappingName="outputMapping"
          formVariables={variablesChoices}
          dmnVariables={dmnParams.outputs}
        />
      </div>
    </div>
  );
};

export default DMNParametersForm;
