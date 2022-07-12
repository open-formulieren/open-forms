import sortBy from 'lodash/sortBy';
import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import {useIntl, FormattedMessage} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
import FAIcon from '../FAIcon';
import Trigger from './logic/Trigger';
import ActionSet from './logic/actions/ActionSet';
import ButtonContainer from '../forms/ButtonContainer';
import Fieldset from '../forms/Fieldset';
import AdvancedTrigger from './logic/AdvancedTrigger';
import DataPreview from './logic/DataPreview';
import DSLEditorNode from './logic/DSLEditorNode';
import LogicTypeSelection from './logic/LogicTypeSelection';
import {ValidationErrorContext} from '../forms/ValidationErrors';
import StepSelection, {useFormStep} from './StepSelection';

const EMPTY_RULE = {
  uuid: '',
  _generatedId: '', // consumers should generate this, as it's used for the React key prop if no uuid exists
  _logicType: '',
  form: '',
  order: null,
  jsonLogicTrigger: {'': [{var: ''}, null]},
  isAdvanced: false,
  actions: [],
};

const parseValidationErrors = errors => {
  let parsedErrors = {};
  for (const [errorName, errorReason] of errors) {
    const errorNameBits = errorName.split('.');
    if (errorNameBits[0] === 'logicRules') {
      _.set(parsedErrors, errorNameBits.slice(1), errorReason);
    }
  }
  return parsedErrors;
};

const FormLogic = ({logicRules = [], onChange, onDelete, onAdd}) => {
  // ensure they're sorted
  logicRules = sortBy(logicRules, ['order']);
  return (
    <Fieldset
      title={<FormattedMessage description="Logic fieldset title" defaultMessage="Logic" />}
    >
      <FormLogicRules rules={logicRules} onAdd={onAdd} onChange={onChange} onDelete={onDelete} />
    </Fieldset>
  );
};

FormLogic.propTypes = {
  logicRules: PropTypes.arrayOf(PropTypes.object).isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onAdd: PropTypes.func.isRequired,
};

const FormLogicRules = ({rules, onAdd, onChange, onDelete}) => {
  const validationErrors = parseValidationErrors(useContext(ValidationErrorContext));
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

const Rule = ({
  _logicType,
  order,
  jsonLogicTrigger,
  triggerFromStep: triggerFromStepIdentifier,
  actions,
  isAdvanced,
  onChange,
  onDelete,
  errors = {},
}) => {
  const intl = useIntl();
  const [displayAdvancedOptions, setDisplayAdvancedOptions] = useState(false);
  const triggerFromStep = useFormStep(triggerFromStepIdentifier);

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

  const TriggerComponent = isAdvanced ? AdvancedTrigger : Trigger;

  return (
    <div className="logic-rule">
      <div className="logic-rule__actions actions actions--vertical actions--align-top">
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
        <FAIcon
          icon="gear"
          title={intl.formatMessage({
            description: 'Logic rule advanced options icon title',
            defaultMessage: 'Advanced options',
          })}
          extraClassname="icon actions__action"
          onClick={() => setDisplayAdvancedOptions(!displayAdvancedOptions)}
        />
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
                  value={triggerFromStepIdentifier || ''}
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

            <DataPreview data={jsonLogicTrigger} />
          </div>
        )}

        <div className="logic-trigger-container">
          <TriggerComponent
            name="jsonLogicTrigger"
            logic={jsonLogicTrigger}
            onChange={onChange}
            error={errors.jsonLogicTrigger}
          />

          {triggerFromStep && (
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
    </div>
  );
};

Rule.propTypes = {
  _logicType: PropTypes.oneOf(['', 'simple', 'advanced']), // TODO: dmn in the future
  order: PropTypes.number.isRequired,
  jsonLogicTrigger: PropTypes.object,
  triggerFromStep: PropTypes.string,
  actions: PropTypes.arrayOf(PropTypes.object),
  isAdvanced: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  errors: PropTypes.object,
};

export {FormLogic, EMPTY_RULE};
