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

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {filterErrors, getChoicesFromSchema} from './utils';

const ObjectsApiOptionsForm = ({index, name, label, schema, formData, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const validationErrors = useContext(ValidationErrorContext);
  const {objectsApiGroup} = schema.properties;
  const apiGroupChoices = getChoicesFromSchema(objectsApiGroup.enum, objectsApiGroup.enumNames);
  const numErrors = filterErrors(name, validationErrors).length;
  const defaultGroup = apiGroupChoices.length === 1 ? apiGroupChoices[0][0] : undefined;

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
              description="Objects API registration options modal title"
              defaultMessage="Plugin configuration: Objects API"
            />
          }
          closeModal={() => setModalOpen(false)}
          extraModifiers={['large']}
        >
          <Formik
            initialValues={{
              ...formData,
              // Ensure that if there's only one option, it is automatically selected.
              objectsApiGroup: formData.objectsApiGroup ?? defaultGroup,
            }}
            onSubmit={(values, actions) => {
              onChange({formData: values});
              actions.setSubmitting(false);
              setModalOpen(false);
            }}
          >
            {({handleSubmit}) => (
              <>
                <ObjectsApiOptionsFormFields
                  index={index}
                  name={name}
                  apiGroupChoices={apiGroupChoices}
                />

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

ObjectsApiOptionsForm.propTypes = {
  index: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  schema: PropTypes.shape({
    properties: PropTypes.shape({
      objectsApiGroup: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.number).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }).isRequired,
  }).isRequired,
  formData: PropTypes.shape({
    version: PropTypes.number,
    objectsApiGroup: PropTypes.number,
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.number,
    updateExistingObject: PropTypes.bool,
    productaanvraagType: PropTypes.string,
    informatieobjecttypeSubmissionReport: PropTypes.string,
    uploadSubmissionCsv: PropTypes.bool,
    informatieobjecttypeSubmissionCsv: PropTypes.string,
    informatieobjecttypeAttachment: PropTypes.string,
    organisatieRsin: PropTypes.string,
    contentJson: PropTypes.string,
    paymentStatusUpdateJson: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default ObjectsApiOptionsForm;
