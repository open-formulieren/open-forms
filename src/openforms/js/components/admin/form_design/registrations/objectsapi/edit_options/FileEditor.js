import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import {DocumentType} from 'components/admin/form_design/registrations/objectsapi/fields/DocumentTypes';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';
import ErrorMessage from 'components/errors/ErrorMessage';

import {useGetDocumentTypes, useResolveCatalogue} from '../hooks';
import {ShowJSONSchemaToggle, TargetPath} from './generic';
import {useFetchTargetPaths, useVariableJsonSchema} from './hooks';

/**
 * Registration options UI/editor for file components.
 */
const FileEditor = ({
  variable,
  component,
  namePrefix,
  components,
  mappedVariable,
  objecttype,
  objectsApiGroup = null,
  objecttypeVersion,
  backendOptions,
}) => {
  const {catalogue = undefined} = backendOptions;
  const isComponentForVariable = component?.key === variable.key;

  const variableSchema = useVariableJsonSchema(variable, components);
  const {
    loading: loadingTargetPaths,
    targetPaths,
    error,
  } = useFetchTargetPaths({
    objectsApiGroup,
    objecttype,
    objecttypeVersion,
    variableJsonSchema: variableSchema,
  });

  if (error) {
    return (
      <ErrorMessage>
        <FormattedMessage
          description="Objects API variable registration configuration API error"
          defaultMessage="Something went wrong when fetching the available target paths"
        />
      </ErrorMessage>
    );
  }

  // the formik state is populated with the backend options, so our path needs to be
  // relative to that.
  // Note that we *could* put information in the variablesMapping.$index.options, but
  // that makes it really hard to handle file components inside edit grids, so we opt
  // for a `files` configuration key and use a consistent approach between v1, v2 objects
  // registration and ZGW APIs registration.
  const filesConfigurationPrefix = `files['${component.key}']`;
  return (
    <>
      {isComponentForVariable && (
        <TargetPath
          namePrefix={namePrefix}
          loading={loadingTargetPaths}
          targetPaths={targetPaths}
        />
      )}
      <CustomDocumentType
        namePrefix={filesConfigurationPrefix}
        objectsApiGroup={objectsApiGroup}
        catalogue={catalogue}
      />
      <OrganizationRSIN namePrefix={filesConfigurationPrefix} />
      <ConfidentialityLevel namePrefix={filesConfigurationPrefix} />
      <Title namePrefix={filesConfigurationPrefix} />
      {isComponentForVariable && (
        <ShowJSONSchemaToggle availablePaths={targetPaths} targetPath={mappedVariable.targetPath} />
      )}
    </>
  );
};

const CustomDocumentType = ({namePrefix, objectsApiGroup, catalogue}) => {
  const {
    loading: loadingCatalogues,
    error: cataloguesError,
    catalogueUrl,
    catalogueValue,
  } = useResolveCatalogue(objectsApiGroup, catalogue);
  if (cataloguesError) throw cataloguesError;

  const {
    loading: loadingDocumentTypes,
    documentTypes,
    error: documentTypesError,
  } = useGetDocumentTypes(objectsApiGroup, catalogueUrl);
  if (documentTypesError) throw documentTypesError;

  return (
    <DocumentType
      name={`${namePrefix}.documentTypeDescription`}
      label={
        <FormattedMessage
          description="Document upload: document type option label"
          defaultMessage="Document type"
        />
      }
      helpText={
        <FormattedMessage
          description="Document upload: document type option help text"
          defaultMessage={`Save the document in the Documents API with the selected
          document type. The document type will be resolved against the
          {catalogueLabel, select,
            empty {specified}
            other {''{catalogueLabel}''}
          } catalogue in the plugin options. If left blank, the
          default attachment document type configured in the plugin options will be used.
          `}
          values={{catalogueLabel: catalogueValue?.label ?? 'empty'}}
        />
      }
      loading={loadingCatalogues || loadingDocumentTypes}
      documentTypes={documentTypes}
      isDisabled={!catalogueUrl}
    />
  );
};

const OrganizationRSIN = ({namePrefix}) => {
  const [props] = useField(`${namePrefix}.organizationRsin`);
  return (
    <FormRow>
      <Field
        name={props.name}
        label={
          <FormattedMessage
            description="Document upload: organizationRsin option label"
            defaultMessage="Organization RSIN"
          />
        }
        helpText={
          <FormattedMessage
            description="Document upload: organizationRsin option help text"
            defaultMessage={`RSIN of the organization that registers the document in
          the Documents API. If left blank, the general configuration is used.`}
          />
        }
      >
        <TextInput {...props} maxLength="9" />
      </Field>
    </FormRow>
  );
};

const CONFIDENTIALITY_OPTIONS = [
  {value: 'openbaar', label: 'Openbaar'},
  {value: 'beperkt_openbaar', label: 'Beperkt openbaar'},
  {value: 'intern', label: 'Intern'},
  {value: 'zaakvertrouwelijk', label: 'Zaakvertrouwelijk'},
  {value: 'vertrouwelijk', label: 'Vertrouwelijk'},
  {value: 'confidentieel', label: 'Confidentieel'},
  {value: 'geheim', label: 'Geheim'},
  {value: 'zeer_geheim', label: 'Zeer geheim'},
];

const ConfidentialityLevel = ({namePrefix}) => (
  <FormRow>
    <Field
      name={`${namePrefix}.confidentialityLevel`}
      label={
        <FormattedMessage
          description="Document upload: confidentialityLevel label"
          defaultMessage="Confidentiality"
        />
      }
      helpText={
        <FormattedMessage
          description="Document upload: confidentialityLevel option help text"
          defaultMessage={`Indication of the level to which extent the document is meant
          to be public. Only provide this if you wish to override the default from the
          configured document type.`}
        />
      }
      noManageChildProps
    >
      <ReactSelect
        name={`${namePrefix}.confidentialityLevel`}
        options={CONFIDENTIALITY_OPTIONS}
        isClearable
      />
    </Field>
  </FormRow>
);

const Title = ({namePrefix}) => {
  const [props] = useField(`${namePrefix}.title`);
  return (
    <FormRow>
      <Field
        name={props.name}
        label={
          <FormattedMessage
            description="Document upload: title option label"
            defaultMessage="Title"
          />
        }
        helpText={
          <FormattedMessage
            description="Document upload: title option help text"
            defaultMessage={`Optional custom title for the document. By default, the
            file name is used.`}
          />
        }
      >
        <TextInput {...props} maxLength="200" />
      </Field>
    </FormRow>
  );
};

/**
 * Stripped down editor for Objects API v1 options - minimal (life) support applies here.
 */
export const FileEditorV1 = ({namePrefix, backendOptions}) => (
  <>
    <CustomDocumentType
      namePrefix={namePrefix}
      objectsApiGroup={backendOptions.objectsApiGroup ?? null}
      catalogue={backendOptions.catalogue}
    />
    <OrganizationRSIN namePrefix={namePrefix} />
    <ConfidentialityLevel namePrefix={namePrefix} />
    <Title namePrefix={namePrefix} />
  </>
);

export default FileEditor;
