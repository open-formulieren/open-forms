import ofDesignTokens from '@open-formulieren/design-tokens/dist/tokens.js';
import {TokenEditor} from 'design-token-editor';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ActionButton, {SubmitAction} from 'components/admin/forms/ActionButton';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';

const DesignTokenValues = ({initialValue = {}, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const [values, setValues] = useState(initialValue);

  const onSubmit = e => {
    e.preventDefault();
    onChange(values);
    setModalOpen(false);
  };

  return (
    <>
      <ActionButton
        onClick={e => {
          e.preventDefault();
          setModalOpen(true);
        }}
        name="edit_design_token_values"
        text={intl.formatMessage({
          description: 'Text on button to open design token editor in modal.',
          defaultMessage: 'Open editor',
        })}
      />

      <FormModal
        title={
          <FormattedMessage
            description="Title of modal to edit design token values"
            defaultMessage="Design token values"
          />
        }
        isOpen={modalOpen}
        closeModal={() => setModalOpen(false)}
        onFormSubmit={onSubmit}
      >
        <TokenEditor
          tokens={ofDesignTokens}
          initialValues={initialValue}
          onChange={newValues => setValues(newValues)}
        />
        <SubmitRow isDefault>
          <SubmitAction
            text={intl.formatMessage({
              description: 'Text on button in modal to save design token values',
              defaultMessage: 'Save changes',
            })}
          />
        </SubmitRow>
      </FormModal>
    </>
  );
};

DesignTokenValues.propTypes = {
  initialValue: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

export default DesignTokenValues;
