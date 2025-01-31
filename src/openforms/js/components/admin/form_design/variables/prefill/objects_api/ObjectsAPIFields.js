/**
 * Prefill configuration form specific to the Objects API prefill plugin.
 *
 * Most other plugins can be configured with the generic form in `./DefaultFields`.
 */
import {useFormikContext} from 'formik';
import {useContext, useEffect} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import {FormContext} from 'components/admin/form_design/Context';
import useConfirm from 'components/admin/form_design/useConfirm';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {LOADING_OPTION} from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';
import VariableMapping from 'components/admin/forms/VariableMapping';
import {
  AuthAttributePath,
  ObjectTypeSelect,
  ObjectTypeVersionSelect,
  ObjectsAPIGroup,
} from 'components/admin/forms/objects_api';
import {FAIcon} from 'components/admin/icons';
import ErrorBoundary from 'components/errors/ErrorBoundary';
import {get} from 'utils/fetch';

import CopyConfigurationFromRegistrationBackend from './CopyConfigurationFromRegistrationBackend';
import SkipOwnershipCheck from './SkipOwnershipCheck';
import useStatus from './useStatus';

const PLUGIN_ID = 'objects_api';

/**
 * Callback to invoke when the API group changes - used to reset the dependent fields.
 */
const onApiGroupChange = prevValues => ({
  ...prevValues,
  options: {
    ...prevValues.options,
    objecttypeUuid: '',
    objecttypeVersion: undefined,
    authAttributePath: undefined,
    variablesMapping: [],
  },
});

/**
 * Callback to invoke when the Object Type changes - used to reset the dependent fields.
 */
const onObjectTypeChange = prevValues => ({
  ...prevValues,
  options: {
    ...prevValues.options,
    objecttypeVersion: undefined,
    authAttributePath: undefined,
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

const ObjectsAPIFields = () => {
  const intl = useIntl();
  // Object with keys the plugin/attribute/options, we process these further to set up
  // the required context for the fields.
  const errors = Object.fromEntries(useContext(ValidationErrorContext));
  const optionsErrors = Object.entries(errors.options ?? {}).map(([key, errs]) => [
    `options.${key}`,
    errs,
  ]);

  const {values, setFieldValue, setValues} = useFormikContext();
  const {
    plugin,
    options: {objecttypeUuid, objecttypeVersion, objectsApiGroup, skipOwnershipCheck},
  } = values;
  const {showCopyButton, toggleShowCopyButton} = useStatus();

  const defaults = {
    objectsApiGroup: null,
    objecttypeUuid: '',
    objecttypeVersion: null,
    skipOwnershipCheck: false,
    authAttributePath: undefined,
    variablesMapping: [],
  };

  // Merge defaults into options if not already set
  useEffect(() => {
    const options = values.options ?? {};
    setFieldValue('options', {...defaults, ...options});
  }, []);

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

  const backends = registrationBackends.filter(elem => elem.backend === 'objects_api');
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
    <ValidationErrorsProvider errors={optionsErrors}>
      {showCopyButton && (
        <CopyConfigurationFromRegistrationBackend
          backends={backends}
          onCopyDone={toggleShowCopyButton}
        />
      )}
      <Fieldset>
        <ObjectsAPIGroup
          apiGroupChoices={apiGroups}
          onChangeCheck={async () => {
            if (!objecttypeUuid) return true;
            const confirmSwitch = await openApiGroupConfirmationModal();
            if (!confirmSwitch) return false;
            setValues(prevValues => ({
              ...prevValues,
              // Trying to set multiple nested values doesn't work, since it sets them
              // with dots in the key
              options: {
                ...prevValues.options,
                authAttributePath: [],
                variablesMapping: [],
              },
            }));
            return true;
          }}
          name="options.objectsApiGroup"
          onApiGroupChange={onApiGroupChange}
        />

        <ErrorBoundary
          // Ensure the error resets when the API group is changed
          key={objectsApiGroup || 'apiGroupErrors'}
          errorMessage={
            <FormattedMessage
              description="Objects API prefill options: object type select error"
              defaultMessage="Something went wrong while retrieving the available object types."
            />
          }
        >
          <ObjectTypeSelect
            name="options.objecttypeUuid"
            apiGroupFieldName="options.objectsApiGroup"
            label={
              <FormattedMessage
                description="Objects API prefill options 'Objecttype' label"
                defaultMessage="Objecttype"
              />
            }
            helpText={
              <FormattedMessage
                description="Objects API prefill options 'Objecttype' helpText"
                defaultMessage="The prefill values will be taken from an object of the selected type."
              />
            }
            onChangeCheck={async () => {
              if (values.options.variablesMapping.length === 0) return true;
              const confirmSwitch = await openObjectTypeConfirmationModal();
              if (!confirmSwitch) return false;
              setValues(prevValues => ({
                ...prevValues,
                // Trying to set multiple nested values doesn't work, since it sets them
                // with dots in the key
                options: {
                  ...prevValues.options,
                  authAttributePath: [],
                  variablesMapping: [],
                },
              }));
              return true;
            }}
            onObjectTypeChange={onObjectTypeChange}
          />
        </ErrorBoundary>

        <ErrorBoundary
          // Ensure the error resets when the objecttype is changed
          key={objecttypeUuid || 'objecttypeErrors'}
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type version select error"
              defaultMessage="Something went wrong while retrieving the available object type versions."
            />
          }
        >
          <ObjectTypeVersionSelect
            name="options.objecttypeVersion"
            label={
              <FormattedMessage
                description="Objects API prefill options 'objecttypeVersion' label"
                defaultMessage="Version"
              />
            }
            apiGroupFieldName="options.objectsApiGroup"
            objectTypeFieldName="options.objecttypeUuid"
          />
        </ErrorBoundary>
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="Objects API ownership check fieldset title"
            defaultMessage="Ownership checks"
          />
        }
      >
        <SkipOwnershipCheck />
        {!skipOwnershipCheck && (
          <AuthAttributePath
            name={'options.authAttributePath'}
            objectsApiGroup={objectsApiGroup}
            objecttypeUuid={objecttypeUuid}
            objecttypeVersion={objecttypeVersion}
            required
            helpText={
              <FormattedMessage
                description="Objects API prefill: authAttributePath helpText"
                defaultMessage={`The property that gets compared with the identifier (e.g. BSN/KVK) of
                the authenticated user. This is important to prevent malicious users
                looking up private information of other people.`}
              />
            }
          />
        )}
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            description="Objects API prefill mappings fieldset title"
            defaultMessage="Mappings"
          />
        }
      >
        <FormRow preventErrorsModifier>
          <VariableMapping
            name="options.variablesMapping"
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
    </ValidationErrorsProvider>
  );
};

ObjectsAPIFields.propTypes = {};

export default ObjectsAPIFields;
