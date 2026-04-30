import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';
import {useIntl} from 'react-intl';

import {DeleteIcon, ErrorIcon, FAIcon} from 'components/admin/icons';

export const FormStepNavSingleItem = ({
  name,
  active = false,
  onActivate,
  onDelete,
  hasErrors = false,
}) => {
  const intl = useIntl();
  const className = classNames('list__item', 'list__item--with-actions', {
    'list__item--active': active,
  });

  const confirmDeleteMessage = intl.formatMessage(
    {
      description: 'Step delete confirmation',
      defaultMessage: 'Are you sure you want to delete the step {step}?',
    },
    {
      step: name,
    }
  );

  const iconTitle = intl.formatMessage({
    description: 'Step validation errors icon title',
    defaultMessage: 'There are validation errors',
  });

  return (
    <li className={className}>
      <button
        type="button"
        onClick={onActivate}
        className="button button--plain list__item-text list__item-text--allow-wrap"
      >
        {hasErrors ? <ErrorIcon text={iconTitle} extraClassname="icon icon--danger" /> : null}
        {name}
      </button>
      <div className="actions">
        <DeleteIcon message={confirmDeleteMessage} onConfirm={onDelete} />
      </div>
    </li>
  );
};

FormStepNavSingleItem.propTypes = {
  name: PropTypes.node.isRequired,
  active: PropTypes.bool.isRequired,
  onActivate: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  hasErrors: PropTypes.bool,
};

export const FormStepNavMultipleItems = ({
  name,
  active = false,
  onActivate,
  onReorder,
  onDelete,
  hasErrors = false,
}) => {
  const intl = useIntl();
  const className = classNames('list__item', 'list__item--with-actions', {
    'list__item--active': active,
  });

  const confirmDeleteMessage = intl.formatMessage(
    {
      description: 'Step delete confirmation',
      defaultMessage: 'Are you sure you want to delete the step {step}?',
    },
    {
      step: name,
    }
  );

  const iconTitle = intl.formatMessage({
    description: 'Step validation errors icon title',
    defaultMessage: 'There are validation errors',
  });

  return (
    <li className={className}>
      <div className="actions actions--vertical">
        <FAIcon
          icon="sort-up"
          title={intl.formatMessage({description: 'Move up icon title', defaultMessage: 'Move up'})}
          extraClassname="fa-lg actions__action"
          onClick={() => onReorder('up')}
        />
        <FAIcon
          icon="sort-down"
          title={intl.formatMessage({
            description: 'Move down icon title',
            defaultMessage: 'Move down',
          })}
          extraClassname="fa-lg actions__action"
          onClick={() => onReorder('down')}
        />
      </div>
      <button
        type="button"
        onClick={onActivate}
        className="button button--plain list__item-text list__item-text--allow-wrap"
      >
        {hasErrors ? <ErrorIcon text={iconTitle} extraClassname="icon icon--danger" /> : null}
        {name}
      </button>
      <div className="actions">
        <DeleteIcon message={confirmDeleteMessage} onConfirm={onDelete} />
      </div>
    </li>
  );
};

FormStepNavMultipleItems.propTypes = {
  name: PropTypes.node.isRequired,
  active: PropTypes.bool.isRequired,
  onActivate: PropTypes.func.isRequired,
  onReorder: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  hasErrors: PropTypes.bool,
};
