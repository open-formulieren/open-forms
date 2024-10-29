/**
 * Prefill configuration form specific to the Objects API prefill plugin.
 *
 * Most other plugins can be configured with the generic form in `./DefaultFields`.
 */
import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import {FormContext} from 'components/admin/form_design/Context';
import useConfirm from 'components/admin/form_design/useConfirm';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {LOADING_OPTION} from 'components/admin/forms/Select';
import VariableMapping from 'components/admin/forms/VariableMapping';
import {
  ObjectTypeSelect,
  ObjectTypeVersionSelect,
  ObjectsAPIGroup,
} from 'components/admin/forms/objects_api';
import {FAIcon} from 'components/admin/icons';
import ErrorBoundary from 'components/errors/ErrorBoundary';
import {get} from 'utils/fetch';

import {ErrorsType} from './types';

const PLUGIN_ID = 'objects_api';

/**
 * Callback to invoke when the API group changes - used to reset the dependent fields.
 */
const onApiGroupChange = prevValues => ({
  ...prevValues,
  prefillOptions: {
    ...prevValues.prefillOptions,
    objecttypeUuid: '',
    objecttypeVersion: undefined,
    variablesMapping: [],
  },
});

// Load the possible prefill properties
// XXX: this would benefit from client-side caching
const getProperties = async (objectsApiGroup, objecttypeUuid, objecttypeVersion) => {
  const endpoint = `/api/v2/prefill/plugins/objects-api/objecttypes/${objecttypeUuid}/versions/${objecttypeVersion}/properties`;
  // XXX: clean up error handling here at some point...
  const response = await get(endpoint, {objects_api_group: objectsApiGroup});
  if (!response.ok) throw response.data;

  return response.data.map(property => [property.targetPath, property.targetPath.join(' > ')]);
};

const ObjectsAPIFields = ({errors}) => {
  const {
    values: {
      plugin,
      prefillOptions: {objecttypeUuid, objecttypeVersion, objectsApiGroup, variablesMapping},
    },
    setFieldValue,
  } = useFormikContext();
  const intl = useIntl();

  const {
    ConfirmationModal: ApiGroupConfirmationModal,
    confirmationModalProps: apiGroupConfirmationModalProps,
    openConfirmationModal: openApiGroupConfirmationModal,
  } = useConfirm();
  const {
    ConfirmationModal: ObjectTypeConfirmationModal,
    confirmationModalProps: objectTypeConfirmationModalProps,
    openConfirmationModal: openObjectTypeConfirmationModal,
  } = useConfirm();

  const {
    plugins: {availablePrefillPlugins},
    registrationBackends,
  } = useContext(FormContext);
  const objectsPlugin = availablePrefillPlugins.find(elem => elem.id === PLUGIN_ID);

  const backend = registrationBackends.find(elem => elem.backend === 'objects_api');
  const {apiGroups} = objectsPlugin.configurationContext;

  const {
    loading,
    value = [],
    error,
  } = useAsync(async () => {
    if (!plugin || !objecttypeUuid || !objecttypeVersion || !objectsApiGroup) return [];
    try {
      return await getProperties(objectsApiGroup, objecttypeUuid, objecttypeVersion);
    } catch (e) {
      throw e;
    }
  }, [plugin, objecttypeUuid, objecttypeVersion, objectsApiGroup]);

  // throw errors to the nearest error boundary
  if (error) throw error;
  const prefillProperties = loading ? LOADING_OPTION : value;

  return (
    <>
      <Fieldset>
        <ObjectsAPIGroup
          apiGroupChoices={apiGroups}
          onChangeCheck={async () => {
            if (variablesMapping.length === 0) return true;
            const confirmSwitch = await openApiGroupConfirmationModal();
            if (!confirmSwitch) return false;
            setFieldValue('prefillOptions.variablesMapping', []);
            return true;
          }}
          name="prefillOptions.objectsApiGroup"
          onApiGroupChange={onApiGroupChange}
        />

        <ErrorBoundary
          // Ensure the error resets when the API group is changed
          key={objectsApiGroup}
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type select error"
              defaultMessage="Something went wrong while retrieving the available object types."
            />
          }
        >
          <ObjectTypeSelect
            name="prefillOptions.objecttypeUuid"
            apiGroupFieldName="prefillOptions.objectsApiGroup"
            versionFieldName="prefillOptions.objecttypeVersion"
            onChangeCheck={async () => {
              if (variablesMapping.length === 0) return true;
              const confirmSwitch = await openObjectTypeConfirmationModal();
              if (!confirmSwitch) return false;
              setFieldValue('prefillOptions.variablesMapping', []);
              return true;
            }}
          />
        </ErrorBoundary>

        <ErrorBoundary
          // Ensure the error resets when the objecttype is changed
          key={objecttypeUuid}
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type version select error"
              defaultMessage="Something went wrong while retrieving the available object type versions."
            />
          }
        >
          <ObjectTypeVersionSelect
            name="prefillOptions.objecttypeVersion"
            apiGroupFieldName="prefillOptions.objectsApiGroup"
            objectTypeFieldName="prefillOptions.objecttypeUuid"
          />
        </ErrorBoundary>

        {backend ? (
          <button
            type="button"
            className="button"
            onClick={e => {
              e.preventDefault();
              const confirmed = window.confirm(
                intl.formatMessage({
                  description: `Objects API prefill configuration: warning message
                    when copying the config from registration backend`,
                  defaultMessage: `Copying the configuration from the registration
                  backend will clear the existing configuration. Are you sure you want to continue?`,
                })
              );
              if (confirmed) {
                setFieldValue('prefillOptions.objectsApiGroup', backend.options.objectsApiGroup);
                setFieldValue('prefillOptions.objecttypeUuid', backend.options.objecttype);
                setFieldValue(
                  'prefillOptions.objecttypeVersion',
                  backend.options.objecttypeVersion
                );
              }
            }}
            // admin style overrides...
            style={{
              marginTop: '2em',
              paddingInline: '15px',
              paddingBlock: '10px',
            }}
          >
            <FormattedMessage
              description="Copy Objects API prefill configuration from registration backend"
              defaultMessage="Copy configuration from registration backend"
            />
          </button>
        ) : null}
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="Objects API prefill mappings fieldset title"
            defaultMessage="Mappings"
          />
        }
      >
        <FormRow>
          <VariableMapping
            name="prefillOptions.variablesMapping"
            loading={loading}
            directionIcon={<FAIcon icon="arrow-left-long" aria-hidden="true" />}
            variableName="variableKey"
            propertyName="targetPath"
            propertyChoices={prefillProperties}
            propertyHeading={
              <FormattedMessage
                description="Prefill / Objects API: column header for object type property selection"
                defaultMessage="Source path"
              />
            }
            propertySelectLabel={intl.formatMessage({
              description:
                'Prefill / Objects API: accessible label for object type property selection',
              defaultMessage: 'Select a property from the object type',
            })}
          />
        </FormRow>
      </Fieldset>

      <ApiGroupConfirmationModal
        {...apiGroupConfirmationModalProps}
        message={
          <FormattedMessage
            description="Objects API registration options: warning message when changing the api group"
            defaultMessage="Changing the api group will remove the existing variables mapping. Are you sure you want to continue?"
          />
        }
      />
      <ObjectTypeConfirmationModal
        {...objectTypeConfirmationModalProps}
        message={
          <FormattedMessage
            description="Objects API registration options: warning message when changing the object type"
            defaultMessage="Changing the objecttype will remove the existing variables mapping. Are you sure you want to continue?"
          />
        }
      />
    </>
  );
};

ObjectsAPIFields.propTypes = {
  errors: PropTypes.shape({
    plugin: ErrorsType,
  }).isRequired,
};

export default ObjectsAPIFields;
