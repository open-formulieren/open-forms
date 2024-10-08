import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import {
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
  const {
    values: {variablesMapping = []},
    setFieldValue,
  } = useFormikContext();

  return (
    <>
      <Fieldset>
        <ObjectsAPIGroup
          apiGroupChoices={apiGroupChoices}
          onChangeCheck={() => {
            if (variablesMapping.length === 0) return true;
            const confirmSwitch = window.confirm(
              intl.formatMessage({
                description:
                  'Objects API registration options: warning message when changing the api group',
                defaultMessage: `Changing the api group will remove the existing variables mapping.
                Are you sure you want to continue?`,
              })
            );
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
            onChangeCheck={() => {
              if (variablesMapping.length === 0) return true;
              const confirmSwitch = window.confirm(
                intl.formatMessage({
                  description:
                    'Objects API registration options: warning message when changing the object type',
                  defaultMessage: `Changing the objecttype will remove the existing variables mapping.
                  Are you sure you want to continue?`,
                })
              );
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
          <ObjectTypeVersionSelect />
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
        <OrganisationRSIN />
      </Fieldset>
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
