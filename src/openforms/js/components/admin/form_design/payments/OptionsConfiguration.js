import {Formik} from 'formik';
import PropTypes from 'prop-types';
import {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ErrorIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';

// TODO: see if we can merge this with the registration options configuration component?
const OptionsConfiguration = ({
  numErrors,
  modalTitle,
  initialFormData,
  onSubmit,
  modalSize = '',
  children,
}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  return (
    <Field
      name="form.paymentBackendOptions"
      label={
        <FormattedMessage
          description="Payment backend options label"
          defaultMessage="Payment backend options"
        />
      }
    >
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
              description="Link label to open payment provider options modal"
              defaultMessage="Configure options"
            />
          </button>
          {numErrors > 0 && (
            <ErrorIcon
              text={intl.formatMessage(
                {
                  description:
                    'Payment provider validation errors icon next to button to configure options',
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
          title={modalTitle}
          closeModal={() => setModalOpen(false)}
          extraModifiers={modalSize ? [modalSize] : undefined}
        >
          <Formik
            initialValues={initialFormData}
            onSubmit={(values, actions) => {
              onSubmit(values);
              actions.setSubmitting(false);
              setModalOpen(false);
            }}
          >
            {({handleSubmit}) => (
              <>
                {children}

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

OptionsConfiguration.propTypes = {
  modalTitle: PropTypes.node.isRequired,
  numErrors: PropTypes.number.isRequired,
  initialFormData: PropTypes.object.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

export default OptionsConfiguration;
