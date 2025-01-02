import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextArea, TextInput} from 'components/admin/forms/Inputs';
import {
  ObjectTypeSelect,
  ObjectTypeVersionSelect,
  ObjectsAPIGroup,
} from 'components/admin/forms/objects_api';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {
  AuthAttributePath,
  DocumentTypesFieldet,
  LegacyDocumentTypesFieldet,
  OrganisationRSIN,
  UpdateExistingObject,
  UploadSubmissionCsv,
} from './fields';

/**
 * Callback to invoke when the API group changes - used to reset the dependent fields.
 */
const onApiGroupChange = prevValues => ({
  ...prevValues,
  objecttype: '',
  objecttypeVersion: undefined,
  authAttributePath: undefined,
});

/**
 * Callback to invoke when the Object Type changes - used to reset the dependent fields.
 */
const onObjectTypeChange = prevValues => ({
  ...prevValues,
  objecttypeVersion: undefined,
  authAttributePath: undefined,
});

const LegacyConfigFields = ({apiGroupChoices}) => {
  const {
    values: {
      objectsApiGroup = null,
      objecttype = '',
      objecttypeVersion = null,
      updateExistingObject = false,
    },
  } = useFormikContext();

  return (
    <>
      <Fieldset>
        <ObjectsAPIGroup apiGroupChoices={apiGroupChoices} onApiGroupChange={onApiGroupChange} />
        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="Legacy Objects API registrations options: unknown error"
              defaultMessage={`Something went wrong retrieving the available object types and/or versions.
              Please check that the services in the selected API group are configured correctly.`}
            />
          }
        >
          <ObjectTypeSelect
            label={
              <FormattedMessage
                description="Objects API registration options 'Objecttype' label"
                defaultMessage="Objecttype"
              />
            }
            helpText={
              <FormattedMessage
                description="Objects API registration options 'Objecttype' helpText"
                defaultMessage="The registration result will be an object from the selected type."
              />
            }
            onObjectTypeChange={onObjectTypeChange}
          />
          <ObjectTypeVersionSelect
            label={
              <FormattedMessage
                description="Objects API registration options 'objecttypeVersion' label"
                defaultMessage="Version"
              />
            }
          />
        </ErrorBoundary>
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="Objects registration: object definition"
            defaultMessage="Object and/or product request definition"
          />
        }
        collapsible
        initialCollapsed={false}
      >
        <ProductAanvraag />
        <ContentJSON />
        <PaymentStatusUpdateJSON />
      </Fieldset>

      <ErrorBoundary
        errorMessage={
          <FormattedMessage
            description="Objects API registrations options: document types selection error"
            defaultMessage="Something went wrong while retrieving the available catalogues and/or document types."
          />
        }
      >
        <DocumentTypesFieldet />
      </ErrorBoundary>

      <LegacyDocumentTypesFieldet />

      <Fieldset
        title={
          <FormattedMessage
            description="Objects registration: update existing objects settings"
            defaultMessage="Update existing objects"
          />
        }
        collapsible
        fieldNames={['updateExistingObject', 'authAttributePath']}
      >
        <UpdateExistingObject />
        <AuthAttributePath />
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="Objects registration: other options"
            defaultMessage="Other options"
          />
        }
        collapsible
        fieldNames={['organisatieRsin']}
      >
        <UploadSubmissionCsv />
        <OrganisationRSIN />
      </Fieldset>
    </>
  );
};

LegacyConfigFields.propTypes = {
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.number, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
};

const ProductAanvraag = () => {
  const [fieldProps] = useField('productaanvraagType');
  return (
    <FormRow>
      <Field
        name="productaanvraagType"
        label={
          <FormattedMessage
            description="Legacy objects API registration options: 'productaanvraagType' label"
            defaultMessage="Product request type"
          />
        }
        helpText={
          <FormattedMessage
            description="Legacy objects API registration options: 'productaanvraagType' helpText"
            defaultMessage="Name of the product request type. It is available in the JSON template as the 'productaanvraag_type' variable."
          />
        }
      >
        <TextInput id="id_productaanvraagType" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

const JSONTemplateField = ({name, label, helpText}) => {
  const [fieldProps] = useField(name);
  return (
    <FormRow>
      <Field name={name} label={label} helpText={helpText}>
        <TextArea
          id={`id_${name}`}
          rows={5}
          cols={85}
          {...fieldProps}
          style={{fontFamily: 'monospace'}}
        />
      </Field>
    </FormRow>
  );
};

JSONTemplateField.propTypes = {
  name: PropTypes.oneOf(['contentJson', 'paymentStatusUpdateJson']).isRequired,
  label: PropTypes.node.isRequired,
  helpText: PropTypes.node,
};

export const ContentJSON = () => (
  <JSONTemplateField
    name="contentJson"
    label={
      <FormattedMessage
        description="Legacy objects API registration options: 'contentJSON' label"
        defaultMessage="JSON content template"
      />
    }
    helpText={
      <FormattedMessage
        description="Legacy objects API registration options: 'contentJSON' helpText"
        defaultMessage="JSON template for the body of the request sent to the Objects API."
      />
    }
  />
);

const PaymentStatusUpdateJSON = () => (
  <JSONTemplateField
    name="paymentStatusUpdateJson"
    label={
      <FormattedMessage
        description="Legacy objects API registration options: 'paymentStatusUpdateJson' label"
        defaultMessage="Payment status update JSON template"
      />
    }
    helpText={
      <FormattedMessage
        description="Legacy objects API registration options: 'paymentStatusUpdateJson' helpText"
        defaultMessage={`This template is evaluated with the submission data when
        the payment is received. The resulting JSON is sent to the objects API to
        update (the payment fields of) the earlier created object.`}
      />
    }
  />
);

export default LegacyConfigFields;
