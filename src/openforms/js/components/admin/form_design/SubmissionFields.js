import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {APIContext} from 'components/admin/form_design/Context';
import {FORM_ENDPOINT} from 'components/admin/form_design/constants';
import ActionButton from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {NumberInput} from 'components/admin/forms/Inputs';
import {FormException} from 'utils/exception';
import {patch} from 'utils/fetch';

import useConfirm from './useConfirm';

export const SubmissionLimitFields = ({submissionLimit, formUuid, onChange}) => {
  const intl = useIntl();
  const {csrftoken} = useContext(APIContext);
  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();

  const handleChange = event => {
    const {name, value: initialValue} = event.target;
    // the backend must receive a value or null since it's a nullable integer field
    const value = initialValue === '' ? null : initialValue;
    const updatedEvent = {...event, target: {...event.target, name, value}};
    onChange(updatedEvent);
  };

  const resetCounter = async () => {
    try {
      const resetResult = await patch(
        `${FORM_ENDPOINT}/${formUuid}`,
        csrftoken,
        {submissionCounter: 0},
        true
      );
      if (!resetResult.ok) {
        throw new FormException(
          'An error occurred while trying to reset the counter.',
          resetResult.data
        );
      }
      return resetResult.data;
    } catch (e) {
      return null;
    }
  };

  return (
    <>
      <Fieldset>
        <FormRow>
          <Field
            name="form.submissionLimit"
            label={
              <FormattedMessage
                description="Form submissionLimit field label"
                defaultMessage="Maximum allowed number of submissions"
              />
            }
            helpText={
              <FormattedMessage
                description="Form submissionLimit field help text"
                defaultMessage="The maximum number of allowed submissions for this form. Leave this empty if no limit is needed."
              />
            }
          >
            <NumberInput value={submissionLimit || null} onChange={handleChange} min="0" />
          </Field>
        </FormRow>
        <FormRow>
          <ActionButton
            type="button"
            className="default"
            text={intl.formatMessage({
              description: 'Reset submissions counter',
              defaultMessage: 'Reset submissions counter',
            })}
            onClick={async event => {
              event.preventDefault();
              const result = await openConfirmationModal();
              if (!result) return;
              await resetCounter();
            }}
          />
        </FormRow>
      </Fieldset>

      <ConfirmationModal
        {...confirmationModalProps}
        message={
          <FormattedMessage
            description="Reset the submissions counter confirmation message"
            defaultMessage="You are about to reset the submissions counter and this action is irreversible. Are you sure that you want to do this?"
          />
        }
      />
    </>
  );
};

SubmissionLimitFields.propTypes = {
  submissionLimit: PropTypes.number,
  formUuid: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};
