import {Formik} from 'formik';
import PropTypes from 'prop-types';
import {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ErrorIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';

/**
 * A generic container/wrapper for configuration options that display in a modal,
 * after clicking the button to configure the options. Next to the button the number
 * of validation errors is displayed.
 *
 * This relies on form state being managed with Formik. Pass the actual configuration
 * fields as children.
 */
const ModalOptionsConfiguration = ({
  name,
  label,
  numErrors,
  modalTitle,
  initialFormData,
  onSubmit,
  modalSize = 'large',
  children,
}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
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
                  description:
                    'Registration validation errors icon next to button to configure options',
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

ModalOptionsConfiguration.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  modalTitle: PropTypes.node.isRequired,
  numErrors: PropTypes.number.isRequired,
  initialFormData: PropTypes.object.isRequired,
  onSubmit: PropTypes.func.isRequired,
  modalSize: PropTypes.oneOf(['', 'small', 'large']),
};

export default ModalOptionsConfiguration;
