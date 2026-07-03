import {Formik} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';

import AdditionalFormConfigurationField from './AdditionalFormConfigurationField';
import FormConfigurationField from './FormConfigurationField';
import RemoveSensitiveContentField from './RemoveSensitiveContentField';
import {
  useAdditionalFormConfigurationOptions,
  useFormConfigurationOptions,
} from './useExportOptions';

const ExportOptionsModal = ({isOpen, onSubmit, onCloseModal}) => {
  const intl = useIntl();
  const formConfigurationOptions = useFormConfigurationOptions();
  const additionalFormConfigurationOptions = useAdditionalFormConfigurationOptions();

  return (
    <FormModal
      isOpen={isOpen}
      title={
        <FormattedMessage
          defaultMessage="Export options"
          description="Form export options modal title"
        />
      }
      closeModal={onCloseModal}
      extraModifiers={['large']}
    >
      <Formik
        initialValues={{
          removeSensitiveContent: true,
          formConfiguration: formConfigurationOptions,
          additionalFormConfiguration: [],
        }}
        onSubmit={(values, actions) => {
          onSubmit(values);
          actions.setSubmitting(false);
          onCloseModal();
        }}
      >
        {({handleSubmit}) => (
          <>
            <Fieldset
              title={
                <FormattedMessage
                  defaultMessage="Security"
                  description="Form export 'security' options fieldset title"
                />
              }
            >
              <FormRow>
                <RemoveSensitiveContentField name="removeSensitiveContent" />
              </FormRow>
            </Fieldset>

            {formConfigurationOptions.length || additionalFormConfigurationOptions.length ? (
              <Fieldset
                title={
                  <FormattedMessage
                    defaultMessage="Export file content"
                    description="Form export 'export file content' options fieldset title"
                  />
                }
              >
                {formConfigurationOptions.length && (
                  <FormRow>
                    <FormConfigurationField name="formConfiguration" />
                  </FormRow>
                )}
                {additionalFormConfigurationOptions.length && (
                  <FormRow>
                    <AdditionalFormConfigurationField name="additionalFormConfiguration" />
                  </FormRow>
                )}
              </Fieldset>
            ) : null}

            <SubmitRow isDefault>
              <SubmitAction
                text={intl.formatMessage({
                  defaultMessage: 'Export form',
                  description: 'Form export options modal submit button text',
                })}
                onClick={event => {
                  event.preventDefault();
                  handleSubmit(event);
                }}
              />
            </SubmitRow>
          </>
        )}
      </Formik>
    </FormModal>
  );
};

ExportOptionsModal.prototype = {
  isOpen: PropTypes.bool.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onCloseModal: PropTypes.func.isRequired,
};

export default ExportOptionsModal;
