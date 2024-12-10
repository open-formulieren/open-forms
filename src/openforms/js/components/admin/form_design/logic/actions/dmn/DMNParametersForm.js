import {parseExpression} from 'feelin';
import {useFormikContext} from 'formik';
import produce from 'immer';
import React, {useEffect} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {useAsync} from 'react-use';

import {DMN_DECISION_DEFINITIONS_PARAMS_LIST} from 'components/admin/form_design/constants';
import VariableMapping from 'components/admin/forms/VariableMapping';
import {FAIcon} from 'components/admin/icons';
import {get} from 'utils/fetch';

import InputsOverview from './InputsOverview';
import {detectMappingProblems, namePattern} from './utils';

const EMPTY_DMN_PARAMS = {
  inputClauses: [],
  inputs: [],
  outputs: [],
};

/**
 * @typedef InputClause
 * @type {object}
 * @property {string} expression - the FEEL expression of the input clause
 * @property {string} label - the human-readable input clause label
 *
 * @typedef {string} OptionValue - The value of a dropdown option.
 * @typedef {string} OptionLabel - The label of a dropdown option.
 * @typedef {[OptionValue, OptionLabel]} Option - A dropdown option.
 */

/**
 * Process the input parameters and their expressions.
 *
 * Each input parameter has a FEEL expression, which itself can be a 'complex'
 * expression requiring individual variables, e.g. `a + b`.
 *
 * Note that expressions are ambiguous without context, `a+b` could mean that input
 * variables `a` and `b` are required, but you could also provide a single input with
 * the name `"a+b"` (this is valid FEEL!).
 *
 * @param  {InputClause[]} params The input clauses extracted from the decision definition.
 * @return {Option[]}        An array of two-tuples (value, label).
 */
const processInputParams = params => {
  const variableExpressionsWithLabels = params
    // check each expression if it can possibly be a valid identifier itself. These
    // should be the most common cases.
    .filter(param => namePattern.test(param.expression))
    .map(param => [param.expression, param.label]);

  // for (simple) expressions, we can grab the explicit label from the input parameter
  // if it's defined. These variables will come up again when we process each expression
  // as a FEEL expression.
  const expressionLabels = Object.fromEntries(variableExpressionsWithLabels);

  // process each expression individually and add the extract variables to the
  // possible variables. This includes the most simple e
  const extractedVariables = [];
  for (const {expression} of params) {
    // docs: https://lezer.codemirror.net/docs/ref/#common.Tree.iterate
    const tree = parseExpression(expression);
    tree.iterate({
      enter({name, from, to, node: {parent}}) {
        if (name !== 'Identifier') return;
        if (parent.name !== 'VariableName') return;

        // check if this var identifier is a function, we need to ignore those.
        const isFunction = parent?.parent.name === 'FunctionInvocation';
        if (isFunction) return;
        const varName = expression.substring(from, to);
        if (extractedVariables.includes(varName)) return;
        extractedVariables.push(varName);
      },
    });
  }

  // We classify the input parameters in two buckets - explicit labels and parsed
  // 'labels' (the same as the variable name, really). Explicit simple input vars with
  // labels (and thus simple expressions) are favoured.
  //
  // It's possible an expression like `a+b` is in variableExpressionsWithLabels without
  // being in extractedVariables - therefore we add those after all the common variable
  // patterns are processed.
  const labeledOptions = [];
  const unlabeledOptions = [];
  for (const varName of extractedVariables) {
    const label = expressionLabels[varName];
    const target = label !== undefined ? labeledOptions : unlabeledOptions;
    target.push([varName, label || varName]);
  }
  const possibleVariables = [...labeledOptions, ...unlabeledOptions];

  // add weird-but-valid labeled expressions that were not picked up by the expression
  // parsing (this parsing is context dependent and cases like `a+b` are ambiguous).
  const weirdCases = variableExpressionsWithLabels.filter(
    ([varName]) => !extractedVariables.includes(varName)
  );

  return possibleVariables.concat(weirdCases);
};

const DMNParametersForm = () => {
  const intl = useIntl();
  const {values, setValues} = useFormikContext();
  const {pluginId, decisionDefinitionId, decisionDefinitionVersion, inputMapping, outputMapping} =
    values;

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

    const inputs = processInputParams(response.data.inputs);

    return {
      inputClauses: response.data.inputs,
      inputs: inputs,
      outputs: response.data.outputs.map(outputParam => [outputParam.name, outputParam.label]),
    };
  }, [pluginId, decisionDefinitionId, decisionDefinitionVersion]);

  // synchronize the input/output mappings in case that parameter references have
  // become stale
  useEffect(() => {
    if (loading || !pluginId || !decisionDefinitionId) return;

    // nothing to do if we don't have any mappings
    if (!(values.inputMapping.length || values.outputMapping.length)) {
      return;
    }

    const {inputs, outputs} = dmnParams;
    const _inputs = inputs.map(([value]) => value);
    const _outputs = outputs.map(([value]) => value);

    let needsUpdate = false;

    const newValues = produce(values, draft => {
      for (const mapping of draft.inputMapping) {
        if (_inputs.includes(mapping.dmnVariable)) continue;
        needsUpdate = true;
        mapping.dmnVariable = '';
      }

      for (const mapping of draft.outputMapping) {
        if (_outputs.includes(mapping.dmnVariable)) continue;
        needsUpdate = true;
        mapping.dmnVariable = '';
      }
    });
    if (needsUpdate) {
      setValues(newValues);
    }
  }, [
    loading,
    values,
    setValues,
    pluginId,
    decisionDefinitionId,
    decisionDefinitionVersion,
    dmnParams,
  ]);

  const dmnVariableColumnLabel = intl.formatMessage({
    description: 'DMN variable label',
    defaultMessage: 'DMN variable',
  });
  const dmnVariableSelectAriaLabel = intl.formatMessage({
    description: 'Accessible label for DMN variable dropdown',
    defaultMessage: 'DMN variable',
  });

  return (
    <div className="logic-dmn">
      <div className="logic-dmn__mapping-config">
        <div className="logic-dmn__mapping">
          <h3 className="react-modal__section-title">
            <FormattedMessage defaultMessage="Input mapping" description="Input mapping title" />
          </h3>
          <VariableMapping
            loading={loading}
            name="inputMapping"
            directionIcon={<FAIcon icon="arrow-right-long" aria-hidden="true" />}
            variableName="formVariable"
            propertyChoices={dmnParams.inputs}
            propertyName="dmnVariable"
            propertyHeading={dmnVariableColumnLabel}
            propertySelectLabel={dmnVariableSelectAriaLabel}
            includeStaticVariables
            rowCheck={detectMappingProblems}
          />
        </div>

        <div className="logic-dmn__mapping">
          <h3 className="react-modal__section-title">
            <FormattedMessage defaultMessage="Output mapping" description="Output mapping title" />
          </h3>
          <VariableMapping
            loading={loading}
            name="outputMapping"
            directionIcon={<FAIcon icon="arrow-left-long" aria-hidden="true" />}
            variableName="formVariable"
            propertyChoices={dmnParams.outputs}
            propertyName="dmnVariable"
            propertyHeading={dmnVariableColumnLabel}
            propertySelectLabel={dmnVariableSelectAriaLabel}
            rowCheck={detectMappingProblems}
          />
        </div>
      </div>

      <InputsOverview inputClauses={dmnParams.inputClauses} />
    </div>
  );
};

export default DMNParametersForm;
