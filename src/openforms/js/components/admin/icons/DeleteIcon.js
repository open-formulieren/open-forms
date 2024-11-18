import PropTypes from 'prop-types';
import React from 'react';
import {useIntl} from 'react-intl';

import useConfirm from 'components/admin/form_design/useConfirm';

import FAIcon from './FAIcon';

const DeleteIcon = ({onConfirm, message, icon = 'trash-can'}) => {
  const intl = useIntl();
  const defaultMessage = intl.formatMessage({
    description: 'Default delete confirmation message',
    defaultMessage: 'Are you sure you want to delete this?',
  });
  const confirmMessage = message || defaultMessage;

  const iconTitle = intl.formatMessage({
    description: 'Delete icon title',
    defaultMessage: 'Delete',
  });

  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();
  const onClick = async () => {
    if (await openConfirmationModal()) {
      onConfirm();
    }
  };

  return (
    <>
      <FAIcon
        icon={icon}
        extraClassname="icon icon--danger actions__action"
        title={iconTitle}
        onClick={onClick}
      />
      <ConfirmationModal {...confirmationModalProps} message={confirmMessage} />
    </>
  );
};

DeleteIcon.propTypes = {
  onConfirm: PropTypes.func.isRequired,
  message: PropTypes.string,
  icon: PropTypes.string,
};

export default DeleteIcon;
