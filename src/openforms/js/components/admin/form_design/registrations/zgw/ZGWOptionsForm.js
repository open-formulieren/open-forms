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

import ZGWFormFields from './ZGWOptionsFormFields';
import {filterErrors, getChoicesFromSchema} from './utils';

const ZGWOptionsForm = ({index, name, label, schema, formData, onChange}) => {
  const intl = useIntl();
  const [modalOpen, setModalOpen] = useState(false);
  const validationErrors = useContext(ValidationErrorContext);

  const {zgwApiGroup, zaakVertrouwelijkheidaanduiding} = schema.properties;
  const apiGroupChoices = getChoicesFromSchema(zgwApiGroup.enum, zgwApiGroup.enumNames);
  const confidentialityLevelChoices = getChoicesFromSchema(
    zaakVertrouwelijkheidaanduiding.enum,
    zaakVertrouwelijkheidaanduiding.enumNames
  );

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
              description="ZGW APIs registration options modal title"
              defaultMessage="Plugin configuration: ZGW APIs"
            />
          }
          closeModal={() => setModalOpen(false)}
          extraModifiers={['large']}
        >
          <Formik
            initialValues={{
              ...formData,
              // Ensure that if there's only one option, it is automatically selected.
              zgwApiGroup: formData.zgwApiGroup ?? defaultGroup,
            }}
            onSubmit={(values, actions) => {
              onChange({formData: values});
              actions.setSubmitting(false);
              setModalOpen(false);
            }}
          >
            {({handleSubmit}) => (
              <>
                <ZGWFormFields
                  name={name}
                  apiGroupChoices={apiGroupChoices}
                  confidentialityLevelChoices={confidentialityLevelChoices}
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

ZGWOptionsForm.propTypes = {
  index: PropTypes.number,
  name: PropTypes.string,
  label: PropTypes.node,
  schema: PropTypes.shape({
    properties: PropTypes.shape({
      zgwApiGroup: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.number).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
      zaakVertrouwelijkheidaanduiding: PropTypes.shape({
        enum: PropTypes.arrayOf(PropTypes.string).isRequired,
        enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
      }).isRequired,
    }).isRequired,
  }).isRequired,
  formData: PropTypes.shape({
    zgwApiGroup: PropTypes.number,
    zaaktype: PropTypes.string,
    informatieobjecttype: PropTypes.string,
    organisatieRsin: PropTypes.string,
    zaakVertrouwelijkheidaanduiding: PropTypes.string,
    medewerkerRoltype: PropTypes.string,
    propertyMappings: PropTypes.arrayOf(
      PropTypes.shape({
        componentKey: PropTypes.string,
        eigenschap: PropTypes.string,
      })
    ),
    objecttype: PropTypes.string,
    objecttypeVersion: PropTypes.string,
    contentJson: PropTypes.string,
  }),
  onChange: PropTypes.func.isRequired,
};

export default ZGWOptionsForm;
