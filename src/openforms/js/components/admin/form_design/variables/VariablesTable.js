import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';
import classNames from 'classnames';

import FAIcon from 'components/admin/FAIcon';
import DeleteIcon from 'components/admin/DeleteIcon';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';
import {FormContext} from 'components/admin/form_design/Context';
import {get} from 'utils/fetch';
import Field from 'components/admin/forms/Field';

import {DATATYPES_CHOICES} from './constants';

const SensitiveData = ({isSensitive}) => {
  const intl = useIntl();
  const sensitiveTitle = intl.formatMessage({
    description: 'Is sensitive icon title',
    defaultMessage: 'Is sensitive',
  });
  const notSensitiveTitle = intl.formatMessage({
    description: 'Is not sensitive icon title',
    defaultMessage: 'Is not sensitive',
  });

  return isSensitive ? (
    <FAIcon icon="exclamation-triangle" title={sensitiveTitle} />
  ) : (
    <FAIcon icon="circle-xmark" extraClassname="fa-regular" title={notSensitiveTitle} />
  );
};

const VariableRow = ({index, variable}) => {
  const formContext = useContext(FormContext);
  const formSteps = formContext.formSteps;

  const getFormDefinitionName = formDefinition => {
    for (const step of formSteps) {
      if (step.formDefinition === formDefinition || step._generatedId === formDefinition)
        return step.name;
    }
    return '';
  };

  return (
    <tr className={`row${(index % 2) + 1}`}>
      <td />
      <td>{variable.name}</td>
      <td>{variable.key}</td>
      <td>{getFormDefinitionName(variable.formDefinition)}</td>
      <td>{variable.prefillAttribute}</td>
      <td>{variable.prefillPlugin}</td>
      <td>{variable.dataType}</td>
      <td>
        <SensitiveData isSensitive={variable.isSensitiveData} />
      </td>
      <td>{JSON.stringify(variable.initialValue)}</td>
      <td>{variable.dataFormat}</td>
    </tr>
  );
};

const EditableVariableRow = ({index, variable, onDelete, onChange}) => {
  const intl = useIntl();
  const deleteConfirmMessage = intl.formatMessage({
    description: 'User defined variable deletion confirm message',
    defaultMessage: 'Are you sure you want to delete this variable?',
  });

  const formContext = useContext(FormContext);

  const {availablePrefillPlugins} = formContext.plugins;
  const prefillPluginChoices = availablePrefillPlugins.map(plugin => [plugin.id, plugin.label]);
  const [prefillAttributeChoices, setPrefillAttributeChoices] = useState([]);

  const formSteps = formContext.formSteps;
  const formStepsChoices = formSteps.map(step => {
    if (step.formDefinition) return [step.formDefinition, step.name];

    return [step._generatedId, step.name];
  });

  const onValueChanged = e => {
    onChange(variable.key, e.target.name, e.target.value);
  };

  const updateKey = e => {
    // Key creation taken from FormIO
    let updatedKey = _.camelCase(variable.name).replace(/^[0-9]*/, '');
    onChange(variable.key, 'key', updatedKey);
  };

  const {loading} = useAsync(async () => {
    setPrefillAttributeChoices([]);
    // Load the possible prefill attributes
    if (!variable.prefillPlugin) return;

    const url = `/api/v1/prefill/plugins/${variable.prefillPlugin}/attributes`;
    const response = await get(url);
    if (!response.ok) {
      console.error(response.data);
    }

    setPrefillAttributeChoices(response.data.map(attribute => [attribute.id, attribute.label]));
  }, [variable.prefillPlugin]);

  const hasErrors = Object.entries(variable.errors || {}).length;

  return (
    <tr
      className={classNames('variables-table__row', `row${(index % 2) + 1}`, {
        'variables-table__row--errors': hasErrors,
      })}
    >
      <td>
        <DeleteIcon onConfirm={() => onDelete(variable.key)} message={deleteConfirmMessage} />
      </td>
      <td>
        <Field name="name" errors={variable.errors?.name}>
          <TextInput
            name="name"
            value={variable.name}
            onChange={onValueChanged}
            onBlur={updateKey}
            noVTextField
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.key}>
          <TextInput name="key" value={variable.key} noVTextField={true} disabled={true} />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.formDefinition}>
          <Select
            name="formDefinition"
            choices={formStepsChoices}
            value={variable.formDefinition}
            onChange={onValueChanged}
            allowBlank
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.prefillPlugin}>
          <Select
            name="prefillPlugin"
            choices={prefillPluginChoices}
            value={variable.prefillPlugin}
            onChange={onValueChanged}
            allowBlank
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.prefillAttribute}>
          <Select
            name="prefillAttribute"
            choices={prefillAttributeChoices}
            value={variable.prefillAttribute}
            onChange={onValueChanged}
            disabled={loading || !variable.prefillPlugin}
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.dataType}>
          <Select
            name="dataType"
            choices={DATATYPES_CHOICES}
            translateChoices
            value={variable.dataType}
            onChange={onValueChanged}
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.isSensitiveData}>
          <Checkbox
            name=""
            label=""
            checked={variable.isSensitiveData}
            onChange={e =>
              onValueChanged({target: {name: 'isSensitiveData', value: !variable.isSensitiveData}})
            }
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.initialValue}>
          <TextInput
            name="initialValue"
            value={variable.initialValue || ''}
            onChange={onValueChanged}
            noVTextField
          />
        </Field>
      </td>
      <td>
        <Field name="key" errors={variable.errors?.dataFormat}>
          <TextInput
            name="dataFormat"
            value={variable.dataFormat}
            onChange={onValueChanged}
            noVTextField
          />
        </Field>
      </td>
    </tr>
  );
};

const VariablesTable = ({variables, editable, onChange, onDelete}) => {
  const headColumns = (
    <>
      <HeadColumn content="" />
      <HeadColumn
        content={<FormattedMessage defaultMessage="Name" description="Variable table name title" />}
      />
      <HeadColumn
        content={<FormattedMessage defaultMessage="Key" description="Variable table key title" />}
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Form definition"
            description="Variable table form definition title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Prefill plugin"
            description="Variable table prefill plugin title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Prefill attribute"
            description="Variable table prefill attribute title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Data type"
            description="Variable table data type title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Sensitive data"
            description="Variable table sensitive data title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Initial value"
            description="Variable table initial value title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Data format"
            description="Variable table data format title"
          />
        }
      />
    </>
  );

  return (
    <div className="variables-table">
      <ChangelistTableWrapper headColumns={headColumns} extraModifiers={['fixed']}>
        {variables.map((variable, index) =>
          editable ? (
            <EditableVariableRow
              key={variable.key}
              index={index}
              variable={variable}
              onChange={onChange}
              onDelete={onDelete}
            />
          ) : (
            <VariableRow key={variable.key} index={index} variable={variable} />
          )
        )}
      </ChangelistTableWrapper>
    </div>
  );
};

export default VariablesTable;
