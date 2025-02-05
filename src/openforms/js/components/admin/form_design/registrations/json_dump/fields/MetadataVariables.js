import {useField} from 'formik';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import {getVariableSource} from 'components/admin/form_design/variables/utils';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';
import {ChangelistColumn, ChangelistTable} from 'components/admin/tables';

import {PLUGIN_ID} from '../constants';

const FixedMetadataVariables = () => {
  const [, {value}] = useField('fixedMetadataVariables');
  const {staticVariables, registrationPluginsVariables} = useContext(FormContext);

  // Create table data
  const jsonDumpVariables = registrationPluginsVariables.find(
    v => v.pluginIdentifier === PLUGIN_ID
  ).pluginVariables;
  const relevantVariables = [
    ...staticVariables.map(v => ({
      ...v,
      source: (
        <FormattedMessage
          defaultMessage="Static"
          description="'Static' source label for fixed metadata variables table"
        />
      ),
    })),
    ...jsonDumpVariables.map(v => ({
      ...v,
      source: (
        <FormattedMessage
          defaultMessage="Registration"
          description="'Registration' source label for fixed metadata variables table"
        />
      ),
    })),
  ].filter(v => value.includes(v.key));

  return (
    <FormRow>
      <Field
        name="fixedMetadataVariables"
        label={
          <FormattedMessage
            description="JSON registration options 'fixedMetadataVariables' label"
            defaultMessage="Fixed"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'fixedMetadataVariables' helpText"
            defaultMessage="Variables that are already included."
          />
        }
      >
        <ChangelistTable data={relevantVariables} linkColumn={null}>
          <ChangelistColumn objProp="name">
            <FormattedMessage defaultMessage="Name" description="Fixed metadata table name title" />
          </ChangelistColumn>
          <ChangelistColumn objProp="key">
            <FormattedMessage
              defaultMessage="Key"
              description="Fixed metadata table name key title"
            />
          </ChangelistColumn>
          <ChangelistColumn objProp="source">
            <FormattedMessage
              defaultMessage="Source"
              description="Fixed metadata table source title"
            />
          </ChangelistColumn>
        </ChangelistTable>
      </Field>
    </FormRow>
  );
};

const AdditionalMetadataVariables = () => {
  const [fieldProps] = useField('additionalMetadataVariables');
  const [, {value}] = useField('fixedMetadataVariables');

  return (
    <FormRow>
      <Field
        name="additionalMetadataVariables"
        label={
          <FormattedMessage
            description="JSON registration options 'additionalMetadataVariables' label"
            defaultMessage="Additional"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'additionalMetadataVariables' helpText"
            defaultMessage="Additional variables to include."
          />
        }
        noManageChildProps
      >
        <VariableSelection
          {...fieldProps}
          isMulti
          closeMenuOnSelect={false}
          includeStaticVariables
          filter={variable =>
            getVariableSource(variable) === VARIABLE_SOURCES.static && !value.includes(variable.key)
          } // Only show static variables and variables which are not already required
        />
      </Field>
    </FormRow>
  );
};

export {AdditionalMetadataVariables, FixedMetadataVariables};
