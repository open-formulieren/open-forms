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

import StufZDSOptionsFormFields from './StufZDSOptionsFormFields';
import {filterErrors} from './utils';

const StufZDSOptionsForm = ({name, label, schema, formData, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const validationErrors = useContext(ValidationErrorContext);
  const numErrors = filterErrors(name, validationErrors).length;

  let initialFormData = {...formData};
  const isNew = !Object.keys(formData).length;
  if (isNew) {
    Object.keys(schema.properties).forEach(propertyKey => {
      if (schema.properties[propertyKey].default) {
        initialFormData[propertyKey] = schema.properties[propertyKey].default;
      }
    });
  }

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
              description="Link label to open StUF-ZDS options modal"
              defaultMessage="Configure options"
            />
          </button>
          {numErrors > 0 && (
            <ErrorIcon
              text={intl.formatMessage(
                {
                  description: 'StUF-ZDS registration validation errors icon next to button',
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
              description="StUF-ZDS registration options modal title"
              defaultMessage="Plugin configuration: StUF-ZDS"
            />
          }
          closeModal={() => setModalOpen(false)}
          extraModifiers={['large']}
        >
          <Formik
            initialValues={initialFormData}
            onSubmit={(values, actions) => {
              onChange({formData: values});
              actions.setSubmitting(false);
              setModalOpen(false);
            }}
          >
            {({handleSubmit}) => (
              <>
                <StufZDSOptionsFormFields name={name} schema={schema} />

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

StufZDSOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']),
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  formData: PropTypes.shape({
    paymentStatusUpdateMapping: PropTypes.arrayOf(
      PropTypes.shape({
        formVariable: PropTypes.string,
        stufName: PropTypes.string,
      })
    ),
    zdsDocumenttypeOmschrijvingInzending: PropTypes.string,
    zdsZaakdocVertrouwelijkheid: PropTypes.string,
    zdsZaaktypeCode: PropTypes.string,
    zdsZaaktypeOmschrijving: PropTypes.string,
    zdsZaaktypeStatusCode: PropTypes.string,
    zdsZaaktypeStatusOmschrijving: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default StufZDSOptionsForm;
