import ofDesignTokens from '@open-formulieren/design-tokens/dist/tokens.js';
import {TokenEditor} from 'design-token-editor';
import PropTypes from 'prop-types';
import React, {useState} from 'react';

import ActionButton, {SubmitAction} from 'components/admin/forms/ActionButton';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';

const DesignTokenValues = ({initialValue = {}, onChange}) => {
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
        text="Open editor"
      />

      <FormModal
        title="Design token values"
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
          <SubmitAction text="Save changes" />
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
