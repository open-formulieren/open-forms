import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import DeleteIcon from 'components/admin/DeleteIcon';
import FormModal from 'components/admin/FormModal';
import DSLEditorNode from 'components/admin/form_design/logic/DSLEditorNode';
import DataPreview from 'components/admin/form_design/logic/DataPreview';
import {ACTION_TYPES} from 'components/admin/form_design/logic/constants';
import Select from 'components/admin/forms/Select';

import ServiceFetchConfigurationPicker from '../../variables/ServiceFetchConfigurationPicker';
import {ActionComponent} from './Actions';
import {ActionError, Action as ActionType} from './types';

const Action = ({prefixText, action, errors = {}, onChange, onDelete}) => {
  const intl = useIntl();
  const hasErrors = Object.entries(errors).length > 0;
  const [isModalOpen, setIsModalOpen] = useState(false);

  const closeModal = () => {
    setIsModalOpen(false);
  };

  return (
    <div className="logic-action">
      <div
        className={`logic-action__row ${classNames({'logic-action__row--has-errors': hasErrors})}`}
      >
        <div className="logic-action__actions">
          <DeleteIcon
            onConfirm={onDelete}
            message={intl.formatMessage({
              description: 'Logic rule action deletion confirm message',
              defaultMessage: 'Are you sure you want to delete this action?',
            })}
          />
        </div>

        <div className="logic-action__action">
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

            <button
              type="button"
              className="button"
              onClick={() => {
                setIsModalOpen(true);
              }}
            >
              <FormattedMessage
                description="Button to toggle service fetch configuration modal"
                defaultMessage="Add service fetch configuration"
              />
            </button>

            <FormModal
              isOpen={isModalOpen}
              closeModal={closeModal}
              title={
                <FormattedMessage
                  description="Service fetch configuration selection modal title"
                  defaultMessage="Service fetch configuration"
                />
              }
              extraModifiers={['large']}
            >
              <ServiceFetchConfigurationPicker />
            </FormModal>
          </div>
        </div>
      </div>

      <div className="logic-action__data-preview">
        <DataPreview data={action} />
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
