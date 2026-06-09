import {useField, useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';

import {DocumentTypeSelect} from './fields';
import useCatalogueOptions from './useCatalogueOptions';

const ZGWVariableConfigurationEditor = ({variable, component = undefined}) => {
  if (!component || component?.type !== 'file') {
    throw new Error('Only file components are supported');
  }

  // the formik state is populated with the backend options, so our path needs to be
  // relative to that
  const namePrefix = `files['${variable.key}']`;
  return (
    <Fieldset>
      <DocumentType namePrefix={namePrefix} />
      <OrganizationRSIN namePrefix={namePrefix} />
      <ConfidentialityLevel namePrefix={namePrefix} />
      <Title namePrefix={namePrefix} />
    </Fieldset>
  );
};

const DocumentType = ({namePrefix}) => {
  const {
    values: {caseTypeIdentification = ''},
  } = useFormikContext();
  // load the available catalogues
  const {cataloguesError, catalogueValue, catalogueUrl} = useCatalogueOptions();
  if (cataloguesError) throw cataloguesError;
  return (
    <DocumentTypeSelect
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
          } catalogue and {caseType, select,
            empty {selected}
            other {''{caseType}''}
          } case type in the plugin options. If left blank, the
          default document type configured in the plugin options will be used.
          `}
          values={{
            catalogueLabel: catalogueValue?.label ?? 'empty',
            caseType: caseTypeIdentification || 'empty',
          }}
        />
      }
      catalogueUrl={catalogueUrl}
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
            form name is used.`}
          />
        }
      >
        <TextInput {...props} maxLength="200" />
      </Field>
    </FormRow>
  );
};

export default ZGWVariableConfigurationEditor;
