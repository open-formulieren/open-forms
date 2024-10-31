import {Formik} from 'formik';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import {ErrorIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';

import EmailOptionsFormFields from './EmailOptionsFormFields';
import {filterErrors} from './utils';

const EmailOptionsForm = ({name, label, schema, formData, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  return (
    <Field name={name} label={label}>
      <>
        <span style={{display: 'inline-flex', gap: '10px', alignItems: 'center'}}>
          <button
            type="button"
            className="button"
            onClick={e => {
              e.preventDefault();
              setModalOpen(true);
            }}
            // admin style overrides...
            style={{
              paddingInline: '15px',
              paddingBlock: '10px',
            }}
          >
            <FormattedMessage
              description="Link label to open registration options modal"
              defaultMessage="Configure options"
            />
          </button>

          {numErrors > 0 && (
            <ErrorIcon
              text={intl.formatMessage(
                {
                  description: 'Objects API registration validation errors icon next to button',
                  defaultMessage: `{numErrors, plural,
              one {There is a validation error.}
              other {There are {numErrors} validation errors.}
            }`,
                },
                {numErrors}
              )}
              extraClassname="fa-lg icon icon--danger icon--compact icon--no-pointer"
            />
          )}
        </span>

        <FormModal
          isOpen={modalOpen}
          title={
            <FormattedMessage
              description="Email registration options modal title"
              defaultMessage="Plugin configuration: Email"
            />
          }
          closeModal={() => setModalOpen(false)}
          extraModifiers={['large']}
        >
          <Formik
            initialValues={{
              ...formData,
              // ensure we have a blank row initially
              toEmails: formData.toEmails?.length ? formData.toEmails : [''],
            }}
            onSubmit={(values, actions) => {
              onChange({formData: values});
              actions.setSubmitting(false);
              setModalOpen(false);
            }}
          >
            {({handleSubmit}) => (
              <>
                <EmailOptionsFormFields name={name} schema={schema} />

                <SubmitRow>
                  <SubmitAction
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
      </>
    </Field>
  );
};

EmailOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']),
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  formData: PropTypes.shape({
    attachFilesToEmail: PropTypes.bool,
    attachmentFormats: PropTypes.arrayOf(PropTypes.string),
    emailContentTemplateHtml: PropTypes.string,
    emailContentTemplateText: PropTypes.string,
    emailPaymentSubject: PropTypes.string,
    emailSubject: PropTypes.string,
    paymentEmails: PropTypes.arrayOf(PropTypes.string),
    toEmails: PropTypes.arrayOf(PropTypes.string),
  }),
  onChange: PropTypes.func.isRequired,
};

export default EmailOptionsForm;
