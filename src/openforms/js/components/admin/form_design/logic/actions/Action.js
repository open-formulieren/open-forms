import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useIntl} from 'react-intl';

import DSLEditorNode from 'components/admin/form_design/logic/DSLEditorNode';
import DataPreview from 'components/admin/form_design/logic/DataPreview';
import ToggleCodeIcon from 'components/admin/form_design/logic/ToggleCodeIcon';
import {ACTION_TYPES} from 'components/admin/form_design/logic/constants';
import Select from 'components/admin/forms/Select';
import {DeleteIcon, WarningIcon} from 'components/admin/icons';

import {ActionComponent, detectProblems} from './Actions';
import {ActionError, Action as ActionType} from './types';

const Action = ({prefixText, action, errors = {}, onChange, onDelete}) => {
  const intl = useIntl();
  const [viewMode, setViewMode] = useState('ui');

  const hasErrors = Object.entries(errors).length > 0;
  const problems = detectProblems(action, intl);
  const warningText = intl.formatMessage(
    {
      description: 'Logic action warning icon text',
      defaultMessage: 'Detected some problems in this action: {problems}.',
    },
    {problems: problems.join(', ')}
  );

  let actionDisplay;
  switch (viewMode) {
    case 'ui': {
      actionDisplay = (
        <div className="dsl-editor">
          <DSLEditorNode errors={null}>{prefixText}</DSLEditorNode>

          <DSLEditorNode errors={errors.action?.type}>
            <Select
              name="action.type"
              choices={ACTION_TYPES}
              translateChoices
              allowBlank
              onChange={onChange}
              value={action.action.type}
            />
          </DSLEditorNode>

          <ActionComponent action={action} errors={errors} onChange={onChange} />
        </div>
      );
      break;
    }
    case 'json': {
      actionDisplay = <DataPreview data={action} />;
      break;
    }
    default: {
      throw new Error(`Unknown viewMode '${viewMode}'.`);
    }
  }

  return (
    <div className={classNames('logic-action', {'logic-action--has-errors': hasErrors})}>
      <div className="actions actions-horizontal">
        {problems.length ? <WarningIcon text={warningText} /> : null}
        <DeleteIcon
          onConfirm={onDelete}
          message={intl.formatMessage({
            description: 'Logic rule action deletion confirm message',
            defaultMessage: 'Are you sure you want to delete this action?',
          })}
        />
      </div>

      <div className="logic-action__action">{actionDisplay}</div>
      <div className="logic-action__view-mode-toggle">
        <ToggleCodeIcon viewMode={viewMode} setViewMode={setViewMode} />
      </div>
    </div>
  );
};

Action.propTypes = {
  prefixText: PropTypes.node.isRequired,
  action: ActionType.isRequired,
  errors: ActionError,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default Action;
