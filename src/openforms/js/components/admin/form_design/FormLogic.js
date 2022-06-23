import sortBy from 'lodash/sortBy';
import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {useIntl, FormattedMessage} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
import FAIcon from '../FAIcon';
import Trigger from './logic/Trigger';
import ActionSet from './logic/actions/ActionSet';
import ButtonContainer from '../forms/ButtonContainer';
import Fieldset from '../forms/Fieldset';
import AdvancedTrigger from './logic/AdvancedTrigger';
import {ValidationErrorContext} from '../forms/ValidationErrors';

const EMPTY_RULE = {
  uuid: '',
  _generatedId: '', // consumers should generate this, as it's used for the React key prop if no uuid exists
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
      <FormLogicRules
        rules={logicRules}
        onAdd={() => onAdd({isAdvanced: false})} /* TODO -> make configurable on the rule itself  */
        onChange={onChange}
        onDelete={onDelete}
      />
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

const Rule = ({jsonLogicTrigger, actions, isAdvanced, onChange, onDelete, errors = {}}) => {
  const intl = useIntl();
  const deleteConfirmMessage = intl.formatMessage({
    description: 'Logic rule deletion confirm message',
    defaultMessage: 'Are you sure you want to delete this rule?',
  });

  const TriggerComponent = isAdvanced ? AdvancedTrigger : Trigger;

  return (
    <div className="logic-rule">
      <div className="logic-rule__actions">
        <DeleteIcon onConfirm={onDelete} message={deleteConfirmMessage} />
        {isAdvanced && (
          <FAIcon icon="brain" extraClassname="icon icon--no-pointer" title="advanced" />
        )}
      </div>

      <div className="logic-rule__rule">
        <TriggerComponent
          name="jsonLogicTrigger"
          logic={jsonLogicTrigger}
          onChange={onChange}
          error={errors.jsonLogicTrigger}
        />
        <ActionSet name="actions" actions={actions} onChange={onChange} errors={errors.actions} />
      </div>
    </div>
  );
};

Rule.propTypes = {
  jsonLogicTrigger: PropTypes.object,
  actions: PropTypes.arrayOf(PropTypes.object),
  isAdvanced: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  errors: PropTypes.object,
};

export {FormLogic, EMPTY_RULE};
