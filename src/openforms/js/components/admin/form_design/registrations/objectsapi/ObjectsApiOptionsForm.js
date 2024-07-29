import {Formik} from 'formik';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {FormModal} from 'components/admin/modals';

import ObjectsApiOptionsFormFields from './ObjectsApiOptionsFormFields';
import {getChoicesFromSchema} from './utils';

const ObjectsApiOptionsForm = ({index, name, label, schema, formData, onChange}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const {objectsApiGroup} = schema.properties;
  const apiGroupChoices = getChoicesFromSchema(objectsApiGroup.enum, objectsApiGroup.enumNames);
  return (
    <Field name={name} label={label}>
      <>
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
              objectsApiGroup:
                formData.objectsApiGroup ?? apiGroupChoices.length === 1
                  ? apiGroupChoices[0][0]
                  : undefined,
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
