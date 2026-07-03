import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {useImmer} from 'use-immer';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';

import AdditionalFormConfigurationField from './AdditionalFormConfigurationField';
import FormConfigurationField from './FormConfigurationField';
import RemoveSensitiveContentField from './RemoveSensitiveContentField';

const ExportOptionsModal = ({isOpen, onSubmit, onCloseModal}) => {
  const intl = useIntl();
  const [exportOptions, setExportOptions] = useImmer({
    removeSensitiveContent: true,
    formConfiguration: ['registrationBackends', 'prefill', 'paymentBackend'],
    additionalFormConfiguration: [],
  });

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
      onFormSubmit={event => {
        event.preventDefault();
        onSubmit(exportOptions);
        onCloseModal();
      }}
      extraModifiers={['large']}
    >
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Security"
            description="Form export 'security' options fieldset title"
          />
        }
      >
        <FormRow>
          <RemoveSensitiveContentField
            value={exportOptions.removeSensitiveContent}
            onChange={e => {
              setExportOptions(draft => {
                draft.removeSensitiveContent = e.target.value;
              });
            }}
          />
        </FormRow>
      </Fieldset>
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Export file content"
            description="Form export 'export file content' options fieldset title"
          />
        }
      >
        <FormRow>
          <FormConfigurationField
            selectedFormConfiguration={exportOptions.formConfiguration}
            availableFormConfiguration={['registrationBackends', 'prefill', 'paymentBackend']}
            onChange={e =>
              setExportOptions(draft => {
                const value = e.target.value;

                if (draft.formConfiguration.includes(value)) {
                  draft.formConfiguration = draft.formConfiguration.filter(
                    option => option !== value
                  );
                } else {
                  draft.formConfiguration.push(value);
                }
              })
            }
          />
        </FormRow>
        <FormRow>
          <AdditionalFormConfigurationField
            selectedAdditionalFormConfiguration={exportOptions.additionalFormConfiguration}
            onChange={e =>
              setExportOptions(draft => {
                const value = e.target.value;

                if (draft.additionalFormConfiguration.includes(value)) {
                  draft.additionalFormConfiguration = draft.additionalFormConfiguration.filter(
                    option => option !== value
                  );
                } else {
                  draft.additionalFormConfiguration.push(value);
                }
              })
            }
          />
        </FormRow>
      </Fieldset>

      <SubmitRow isDefault>
        <SubmitAction
          text={intl.formatMessage({
            defaultMessage: 'Export form',
            description: 'Form export options modal submit button text',
          })}
        />
      </SubmitRow>
    </FormModal>
  );
};

ExportOptionsModal.prototype = {
  isOpen: PropTypes.bool.isRequired,
  onSubmit: PropTypes.func.isRequired,
  onCloseModal: PropTypes.func.isRequired,
};

export default ExportOptionsModal;
