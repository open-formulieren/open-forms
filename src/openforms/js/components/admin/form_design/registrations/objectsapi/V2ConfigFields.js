import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext} from 'react';
import {useIntl} from 'react-intl';
import {FormattedMessage} from 'react-intl';

import {FeatureFlagsContext} from 'components/admin/form_design/Context';
import useConfirm from 'components/admin/form_design/useConfirm';
import Fieldset from 'components/admin/forms/Fieldset';
import {
  AuthAttributePath,
  ObjectTypeSelect,
  ObjectTypeVersionSelect,
  ObjectsAPIGroup,
} from 'components/admin/forms/objects_api';
import ErrorBoundary from 'components/errors/ErrorBoundary';

import {
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
  variablesMapping: [],
});

const V2ConfigFields = ({apiGroupChoices}) => {
  const intl = useIntl();
  const {REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION = false} =
    useContext(FeatureFlagsContext);

  const [updateExistingObject] = useField('updateExistingObject');
  const authAttributePathRequired = !!updateExistingObject.value;

  const {
    values: {variablesMapping = []},
    setFieldValue,
  } = useFormikContext();

  const {
    ConfirmationModal: ApiGroupConfirmationModal,
    confirmationModalProps: apiGroupConfirmationModalProps,
    openConfirmationModal: openApiGroupConfirmation,
  } = useConfirm();
  const {
    ConfirmationModal: ObjectTypeConfirmationModal,
    confirmationModalProps: objectTypeConfirmationModalProps,
    openConfirmationModal: openObjectTypeConfirmation,
  } = useConfirm();

  return (
    <>
      <Fieldset>
        <ObjectsAPIGroup
          apiGroupChoices={apiGroupChoices}
          onChangeCheck={async () => {
            if (variablesMapping.length === 0) return true;
            const confirmSwitch = await openApiGroupConfirmation();
            if (!confirmSwitch) return false;
            setFieldValue('variablesMapping', []);
            return true;
          }}
          onApiGroupChange={onApiGroupChange}
        />
        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type select error"
              defaultMessage="Something went wrong while retrieving the available object types."
            />
          }
        >
          <ObjectTypeSelect
            label={intl.formatMessage({
              description: "Objects API registration options 'Objecttype' label",
              defaultMessage: 'Objecttype',
            })}
            helpText={intl.formatMessage({
              description: "Objects API registration options 'Objecttype' helpText",
              defaultMessage: 'The registration result will be an object from the selected type.',
            })}
            onChangeCheck={async () => {
              if (variablesMapping.length === 0) return true;
              const confirmSwitch = await openObjectTypeConfirmation();
              if (!confirmSwitch) return false;
              setFieldValue('variablesMapping', []);
              return true;
            }}
          />
        </ErrorBoundary>

        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type version select error"
              defaultMessage="Something went wrong retrieving the available object type versions."
            />
          }
        >
          <ObjectTypeVersionSelect
            label={intl.formatMessage({
              description: "Objects API registration options 'objecttypeVersion' label",
              defaultMessage: 'Version',
            })}
          />
        </ErrorBoundary>
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
            description="Objects registration: other options"
            defaultMessage="Other options"
          />
        }
        collapsible
        fieldNames={['organisatieRsin']}
      >
        <UploadSubmissionCsv />
        <UpdateExistingObject />
        {REGISTRATION_OBJECTS_API_ENABLE_EXISTING_OBJECT_INTEGRATION ? (
          <AuthAttributePath name={'authAttributePath'} required={authAttributePathRequired} />
        ) : null}
        <OrganisationRSIN />
      </Fieldset>

      <ApiGroupConfirmationModal
        {...apiGroupConfirmationModalProps}
        message={
          <FormattedMessage
            description="Objects API registration options: warning message when changing the api group"
            defaultMessage="Changing the api group will remove the existing variables mapping.
                Are you sure you want to continue?"
          />
        }
      />
      <ObjectTypeConfirmationModal
        {...objectTypeConfirmationModalProps}
        message={
          <FormattedMessage
            description="Objects API registration options: warning message when changing the object type"
            defaultMessage="Changing the objecttype will remove the existing variables mapping.
                  Are you sure you want to continue?"
          />
        }
      />
    </>
  );
};

V2ConfigFields.propTypes = {
  apiGroupChoices: PropTypes.arrayOf(
    PropTypes.arrayOf(
      PropTypes.oneOfType([
        PropTypes.number, // value
        PropTypes.string, // label
      ])
    )
  ).isRequired,
};

export default V2ConfigFields;
