import sortBy from 'lodash/sortBy';
import zip from 'lodash/zip';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';
import useMountedState from 'react-use/esm/useMountedState';
import {useImmerReducer} from 'use-immer';

import Loader from 'components/admin/Loader';
import MessageList from 'components/admin/MessageList';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Fieldset from 'components/admin/forms/Fieldset';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import {DeleteIcon, FAIcon} from 'components/admin/icons';
import ErrorBoundary from 'components/errors/ErrorBoundary';
import jsonPropTypeValidator from 'utils/JsonPropTypeValidator';

import {FormContext, FormLogicContext} from './Context';
import StepSelection, {useFormStep, useFormSteps} from './StepSelection';
import {SERVICES_ENDPOINT, SERVICE_FETCH_CONFIG_ENDPOINT} from './constants';
import {loadFromBackend} from './data';
import AdvancedTrigger from './logic/AdvancedTrigger';
import DSLEditorNode from './logic/DSLEditorNode';
import DataPreview from './logic/DataPreview';
import LogicDescriptionInput from './logic/LogicDescription';
import LogicTypeSelection from './logic/LogicTypeSelection';
import Trigger from './logic/Trigger';
import ActionSet from './logic/actions/ActionSet';
import {detectProblems} from './logic/actions/Actions';
import {parseValidationErrors} from './utils';

const EMPTY_RULE = {
  uuid: '',
  _generatedId: '', // consumers should generate this, as it's used for the React key prop if no uuid exists
  _logicType: '',
  form: '',
  description: '',
  _mayGenerateDescription: true,
  order: null,
  jsonLogicTrigger: {'': [{var: ''}, null]},
  isAdvanced: false,
  actions: [],
};

const initialState = {
  services: [],
  serviceFetchConfigurations: [],
};

function reducer(draft, action) {
  switch (action.type) {
    case 'BACKEND_DATA_LOADED': {
      const {supportingData} = action.payload;

      for (const [stateVar, data] of Object.entries(supportingData)) {
        draft[stateVar] = data;
      }
      break;
    }
  }
}

const FormLogic = ({logicRules = [], onChange, onServiceFetchAdd, onDelete, onAdd}) => {
  const [state, dispatch] = useImmerReducer(reducer, initialState);
  const isMounted = useMountedState();

  const backendDataToLoad = [
    {endpoint: SERVICES_ENDPOINT, stateVar: 'services'},
    {
      endpoint: SERVICE_FETCH_CONFIG_ENDPOINT,
      stateVar: 'serviceFetchConfigurations',
      reshapeData: data => {
        return data.map((element, index) => {
          element.headers = Object.entries(element.headers);
          element.queryParams = Object.entries(element.queryParams);
          return element;
        });
      },
    },
  ];

  const {loading} = useAsync(async () => {
    // TODO: API error handling - this should be done using ErrorBoundary instead of
    // state-changes.
    const backendData = await loadFromBackend(backendDataToLoad);
    const supportingData = Object.fromEntries(
      zip(backendDataToLoad, backendData).map(([plugin, data]) => [plugin.stateVar, data])
    );

    if (!isMounted()) return;
    dispatch({
      type: 'BACKEND_DATA_LOADED',
      payload: {supportingData},
    });
  }, []);

  if (loading) {
    return <Loader />;
  }

  // ensure they're sorted
  logicRules = sortBy(logicRules, ['order']);
  return (
    <FormLogicContext.Provider
      value={{
        services: state.services,
        serviceFetchConfigurations: state.serviceFetchConfigurations,
        onServiceFetchAdd: onServiceFetchAdd,
      }}
    >
      <Fieldset
        title={<FormattedMessage description="Logic fieldset title" defaultMessage="Logic" />}
      >
        <FormLogicRules rules={logicRules} onAdd={onAdd} onChange={onChange} onDelete={onDelete} />
      </Fieldset>
    </FormLogicContext.Provider>
  );
};

FormLogic.propTypes = {
  logicRules: PropTypes.arrayOf(PropTypes.object).isRequired,
  onChange: PropTypes.func.isRequired,
  onServiceFetchAdd: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
};

const FormLogicRules = ({rules, onAdd, onChange, onDelete}) => {
  const validationErrors = parseValidationErrors(useContext(ValidationErrorContext), 'logicRules');
  // FIXME - getting the validation errors by index breaks if you then delete rules/reorder
  // rules -> they're displayed for the wrong rule. When deleting/reordering rules, the
  // validation errors state needs to be re-ordered the same way.
  return (
    <>
      <p style={{padding: '1em 0 0', color: 'var(--body-quiet-color)'}}>
        <FormattedMessage
          description="Logic rules introduction/explanation"
          defaultMessage={`
          The logic rules you set up here are executed in the order that they are defined.
          Please consult the <docs>manual</docs> for more information.
        `}
          values={{
            docs: chunks => (
              <a
                href="https://open-forms.readthedocs.io/en/stable/manual/forms/logic.html"
                target="_blank"
                rel="noopener noreferrer"
              >
                {chunks}
              </a>
            ),
          }}
        />
      </p>

      {rules.map((rule, index) => {
        return (
          <Rule
            key={rule.uuid || rule._generatedId}
            isCreate={!rule.uuid}
            {...rule}
            onChange={onChange.bind(null, index)}
            onDelete={onDelete.bind(null, index)}
            errors={validationErrors[index.toString()]}
          />
        );
      })}
      <ButtonContainer onClick={onAdd}>
        <FormattedMessage description="Add form logic rule button" defaultMessage="Add rule" />
      </ButtonContainer>
    </>
  );
};

FormLogicRules.propTypes = {
  rules: PropTypes.arrayOf(PropTypes.object).isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
};

const RuleBody = ({
  isCreate,
  isAdvanced,
  jsonLogicTrigger,
  actions,
  displayAdvancedOptions,
  setDisplayAdvancedOptions,
  description,
  triggerFromStepIdentifier,
  formStepIdentifiers,
  onChange,
  errors,
  mayGenerateDescription,
}) => {
  const intl = useIntl();
  const [expandExpression, setExpandExpression] = useState(isCreate);
  const [resetRequest, setResetRequest] = useState(0);
  const triggerFromStep = useFormStep(triggerFromStepIdentifier);
  const formSteps = useFormSteps(formStepIdentifiers);
  const {newLogicEvaluationEnabled} = useContext(FormContext);

  // Case in which there is an error: a trigger step was specified, but this step cannot be found in the form
  if (!triggerFromStep && triggerFromStepIdentifier && !newLogicEvaluationEnabled)
    setDisplayAdvancedOptions(true);
  displayAdvancedOptions = displayAdvancedOptions && !newLogicEvaluationEnabled;

  const TriggerComponent = isAdvanced ? AdvancedTrigger : Trigger;

  const onDescriptionGenerated = generatedDescription => {
    let newDescription = intl.formatMessage(
      {
        description: 'Logic expression generated description',
        defaultMessage: 'When {desc}',
      },
      {desc: generatedDescription}
    );

    // backend allows 100 chars max
    if (newDescription.length >= 100) {
      newDescription = `${newDescription.substring(0, 99)}…`;
    }
    onChange({target: {name: 'description', value: newDescription}});
  };

  return (
    <>
      <div className="logic-rule__rule">
        <div className="logic-rule__header">
          <h3 className="logic-rule__heading">
            <FormattedMessage
              description="Logic trigger heading"
              defaultMessage="Trigger condition"
            />
          </h3>
        </div>

        {displayAdvancedOptions && (
          <>
            <div className="logic-rule__advanced">
              <div className="dsl-editor">
                <DSLEditorNode errors={null}>
                  <FormattedMessage
                    description="'Trigger from step' label"
                    defaultMessage="Enable from step: "
                  />
                </DSLEditorNode>

                <DSLEditorNode errors={null}>
                  <StepSelection
                    name="triggerFromStep"
                    value={triggerFromStep?.step?.uuid || triggerFromStepIdentifier || ''}
                    onChange={onChange}
                  />
                  {!triggerFromStepIdentifier && (
                    <>
                      &nbsp;
                      <FormattedMessage
                        description="'Trigger from step' information for when unset"
                        defaultMessage="(checked for every step)"
                      />
                    </>
                  )}
                </DSLEditorNode>
              </div>
            </div>
            {triggerFromStepIdentifier && !triggerFromStep && (
              <MessageList
                messages={[
                  {
                    message: (
                      <FormattedMessage
                        description="Warning missing trigger step"
                        defaultMessage="The selected trigger step could not be found in this form! Please change it!"
                      />
                    ),
                    level: 'warning',
                  },
                ]}
              />
            )}
          </>
        )}

        {newLogicEvaluationEnabled && (
          <div className="logic-rule__advanced">
            <FormattedMessage
              description="Execute on step(s) label"
              defaultMessage="This rule will be executed on step(s): {steps}"
              values={{steps: formSteps.map(step => step.stepName).join(', ')}}
            />
          </div>
        )}

        <div className="logic-trigger-container">
          {isAdvanced ? (
            <div className="logic-trigger-container__description">
              <LogicDescriptionInput
                name="description"
                generationRequest={resetRequest}
                generationAllowed={mayGenerateDescription}
                logicExpression={jsonLogicTrigger}
                value={description}
                onChange={onChange}
                onDescriptionGenerated={onDescriptionGenerated}
                size={100}
                error={errors.description}
                placeholder={intl.formatMessage({
                  description: 'Logic rule description placeholder',
                  defaultMessage: 'Easy to understand description',
                })}
              />

              <div className="actions actions--horizontal">
                <FAIcon
                  icon={expandExpression ? 'chevron-up' : 'chevron-down'}
                  title={intl.formatMessage({
                    description: 'Expand/collapse logic expression icon title',
                    defaultMessage: 'Expand/collapse JsonLogic',
                  })}
                  extraClassname="actions__action"
                  onClick={() => setExpandExpression(!expandExpression)}
                />
                <FAIcon
                  icon="arrows-rotate"
                  title={intl.formatMessage({
                    description: 'Reset logic expression icon title',
                    defaultMessage: 'Reset to default description',
                  })}
                  extraClassname="actions__action"
                  onClick={() => {
                    onChange({target: {name: 'description', value: ''}});
                    setResetRequest(resetRequest + 1);
                  }}
                />
              </div>
            </div>
          ) : null}

          <TriggerComponent
            name="jsonLogicTrigger"
            logic={jsonLogicTrigger}
            onChange={onChange}
            error={errors.jsonLogicTrigger}
            expandExpression={expandExpression}
          />

          {triggerFromStep && !newLogicEvaluationEnabled && (
            <div className="logic-trigger-container__extra-condition">
              <FormattedMessage
                description="Additional 'trigger from step' condition"
                defaultMessage={'and the step "{step}" has been reached'}
                values={{step: triggerFromStep.stepName}}
              />
            </div>
          )}
        </div>

        <ActionSet name="actions" actions={actions} onChange={onChange} errors={errors.actions} />
      </div>
    </>
  );
};

RuleBody.propTypes = {
  isCreate: PropTypes.bool.isRequired,
  isAdvanced: PropTypes.bool.isRequired,
  jsonLogicTrigger: jsonPropTypeValidator,
  actions: PropTypes.arrayOf(PropTypes.object),
  displayAdvancedOptions: PropTypes.bool,
  setDisplayAdvancedOptions: PropTypes.func.isRequired,
  description: PropTypes.string,
  triggerFromStepIdentifier: PropTypes.string,
  formStepIdentifiers: PropTypes.arrayOf(PropTypes.string),
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.object,
  mayGenerateDescription: PropTypes.bool.isRequired,
};

const Rule = ({
  isCreate,
  _logicType,
  description,
  _mayGenerateDescription,
  order,
  jsonLogicTrigger,
  triggerFromStep: triggerFromStepIdentifier,
  actions,
  isAdvanced,
  formSteps: formStepIdentifiers,
  onChange,
  onDelete,
  errors = {},
}) => {
  const intl = useIntl();
  const [displayAdvancedOptions, setDisplayAdvancedOptions] = useState(false);
  const {newLogicEvaluationEnabled} = useContext(FormContext);

  const deleteConfirmMessage = intl.formatMessage({
    description: 'Logic rule deletion confirm message',
    defaultMessage: 'Are you sure you want to delete this rule?',
  });

  // if no logicType has been set yet, we first present the type selection before the
  // actual rule can be set up.
  if (!_logicType) {
    return (
      <LogicTypeSelection
        onChange={selectedType => onChange({target: {name: '_logicType', value: selectedType}})}
        onCancel={onDelete}
      />
    );
  }

  const boundaryErrorMessage = (
    <div className="logic-rule-error">
      <div className="logic-rule-error__text">
        <FormattedMessage
          description="Unexpected error message in logic rule"
          defaultMessage="Something went wrong while rendering this logic rule! For debugging, here is the JSON of the logic rule:"
        />
      </div>

      <div className="logic-rule-error__json">
        <code>
          {JSON.stringify({
            jsonLogicTrigger,
            triggerFromStepIdentifier,
            order,
            actions,
            isAdvanced,
          })}
        </code>
      </div>
    </div>
  );

  return (
    <div className="logic-rule">
      <div className="logic-rule__actions actions actions--vertical actions--align-top">
        {!newLogicEvaluationEnabled && (
          <div className="actions__action-group">
            <FAIcon
              icon="sort-up"
              title={intl.formatMessage({
                description: 'Move up icon title',
                defaultMessage: 'Move up',
              })}
              extraClassname="fa-lg actions__action"
              onClick={() => onChange({target: {name: 'order', value: order - 1}})}
            />
            <FAIcon
              icon="sort-down"
              title={intl.formatMessage({
                description: 'Move down icon title',
                defaultMessage: 'Move down',
              })}
              extraClassname="fa-lg actions__action"
              onClick={() => onChange({target: {name: 'order', value: order + 1}})}
            />
          </div>
        )}
        {!newLogicEvaluationEnabled && (
          <FAIcon
            icon="gear"
            title={intl.formatMessage({
              description: 'Logic rule advanced options icon title',
              defaultMessage: 'Advanced options',
            })}
            extraClassname="icon actions__action"
            onClick={() => setDisplayAdvancedOptions(!displayAdvancedOptions)}
          />
        )}
        <DeleteIcon
          onConfirm={onDelete}
          message={deleteConfirmMessage}
          extraClassname="actions__action"
        />
        {isAdvanced && (
          <FAIcon
            icon="wand-magic-sparkles"
            extraClassname="icon icon--no-pointer"
            title="advanced"
          />
        )}
      </div>

      <ErrorBoundary errorMessage={boundaryErrorMessage}>
        <RuleBody
          isCreate={isCreate}
          isAdvanced={isAdvanced}
          jsonLogicTrigger={jsonLogicTrigger}
          actions={actions}
          triggerFromStepIdentifier={triggerFromStepIdentifier}
          displayAdvancedOptions={displayAdvancedOptions}
          setDisplayAdvancedOptions={setDisplayAdvancedOptions}
          description={description}
          formStepIdentifiers={formStepIdentifiers}
          onChange={onChange}
          errors={errors}
          mayGenerateDescription={_mayGenerateDescription}
        />
      </ErrorBoundary>
    </div>
  );
};

Rule.propTypes = {
  isCreate: PropTypes.bool.isRequired,
  _logicType: PropTypes.oneOf(['', 'simple', 'advanced']), // TODO: dmn in the future
  description: PropTypes.string,
  _mayGenerateDescription: PropTypes.bool.isRequired,
  order: PropTypes.number.isRequired,
  jsonLogicTrigger: jsonPropTypeValidator,
  triggerFromStep: PropTypes.string,
  actions: PropTypes.arrayOf(PropTypes.object),
  isAdvanced: PropTypes.bool.isRequired,
  formSteps: PropTypes.arrayOf(PropTypes.string),
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  errors: PropTypes.object,
};

const detectLogicProblems = (rule, intl) => {
  const problems = [];
  const hasActionProblems = rule.actions.some(action => detectProblems(action, intl).length > 0);
  if (hasActionProblems) {
    problems.push(
      intl.formatMessage({
        description: 'Logic rule warning message about problematic actions.',
        defaultMessage: 'one or more actions are invalid',
      })
    );
  }
  return problems;
};

export {FormLogic, EMPTY_RULE, detectLogicProblems};
