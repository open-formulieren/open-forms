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
  options: {
    ...prevValues.options,
    objecttype: '',
    objecttypeVersion: undefined,
    variablesMapping: [],
  },
});

// Load the possible prefill properties
// XXX: this would benefit from client-side caching
const getProperties = async (objectsApiGroup, objecttype, objecttypeVersion) => {
  const endpoint = `/api/v2/prefill/plugins/objects-api/objecttypes/${objecttype}/versions/${objecttypeVersion}/properties`;
  // XXX: clean up error handling here at some point...
  const response = await get(endpoint, {objects_api_group: objectsApiGroup});
  if (!response.ok) throw response.data;

  return response.data.map(property => [property.targetPath, property.targetPath.join(' > ')]);
};

const ObjectsAPIFields = ({errors}) => {
  const {
    values: {
      plugin,
      options: {objecttype, objecttypeVersion, objectsApiGroup},
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
  } = useContext(FormContext);
  const objectsPlugin = availablePrefillPlugins.find(elem => elem.id === PLUGIN_ID);

  const {apiGroups} = objectsPlugin.configurationContext;

  const {
    loading,
    value = [],
    error,
  } = useAsync(async () => {
    if (!plugin || !objecttype || !objecttypeVersion || !objectsApiGroup) return [];
    try {
      return await getProperties(objectsApiGroup, objecttype, objecttypeVersion);
    } catch (e) {
      throw e;
    }
  }, [plugin, objecttype, objecttypeVersion, objectsApiGroup]);

  // throw errors to the nearest error boundary
  if (error) throw error;
  const prefillProperties = loading ? LOADING_OPTION : value;

  return (
    <>
      <Fieldset>
        <ObjectsAPIGroup
          apiGroupChoices={apiGroups}
          onChangeCheck={async () => {
            if (values.options.variablesMapping.length === 0) return true;
            const confirmSwitch = await openApiGroupConfirmationModal();
            if (!confirmSwitch) return false;
            setFieldValue('options.variablesMapping', []);
            return true;
          }}
          name="options.objectsApiGroup"
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
            name="options.objecttype"
            apiGroupFieldName="options.objectsApiGroup"
            versionFieldName="options.objecttypeVersion"
            onChangeCheck={async () => {
              if (values.options.variablesMapping.length === 0) return true;
              const confirmSwitch = await openObjectTypeConfirmationModal();
              if (!confirmSwitch) return false;
              setFieldValue('options.variablesMapping', []);
              return true;
            }}
          />
        </ErrorBoundary>

        <ErrorBoundary
          errorMessage={
            <FormattedMessage
              description="Objects API registrations options: object type version select error"
              defaultMessage="Something went wrong while retrieving the available object type versions."
            />
          }
        >
          <ObjectTypeVersionSelect
            name="options.objecttypeVersion"
            apiGroupFieldName="options.objectsApiGroup"
            objectTypeFieldName="options.objecttype"
          />
        </ErrorBoundary>
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
            name="options.variablesMapping"
            loading={loading}
            directionIcon={<FAIcon icon="arrow-left-long" aria-hidden="true" />}
            propertyName="prefillProperty"
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
