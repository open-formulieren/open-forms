import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {Checkbox, TextInput} from '../../forms/Inputs';
import Select from '../../forms/Select';
import {DATATYPES_CHOICES} from './constants';
import DeleteIcon from '../../DeleteIcon';

const VariableRow = ({variable}) => {
  return (
    <tr>
      <td>{variable.name}</td>
      <td>{variable.key}</td>
      <td>{variable.prefillAttribute}</td>
      <td>{variable.prefillPlugin}</td>
      <td>{variable.dataType}</td>
      <td>{variable.isSensitiveData}</td>
      <td>{variable.initialValue}</td>
      <td>{variable.dataFormat}</td>
    </tr>
  );
};

const EditableVariableRow = ({variable, onDelete, onChange}) => {
  const intl = useIntl();
  const deleteConfirmMessage = intl.formatMessage({
    description: 'User defined variable deletion confirm message',
    defaultMessage: 'Are you sure you want to delete this variable?',
  });

  const onValueChanged = e => {
    onChange(variable.key, e.target.name, e.target.value);
  };

  return (
    <tr>
      <td>
        <DeleteIcon onConfirm={() => onDelete(variable.key)} message={deleteConfirmMessage} />
      </td>
      <td>
        <TextInput name="name" value={variable.name} onChange={onValueChanged} />
      </td>
      <td>
        <TextInput name="key" value={variable.key} onChange={onValueChanged} />
      </td>
      <td>
        <TextInput name="prefillPlugin" value={variable.prefillPlugin} onChange={onValueChanged} />
      </td>
      <td>
        <TextInput
          name="prefillAttribute"
          value={variable.prefillAttribute}
          onChange={onValueChanged}
        />
      </td>
      <td>
        <Select
          name="dataType"
          choices={DATATYPES_CHOICES}
          translateChoices
          value={variable.dataType}
          onChange={onValueChanged}
        />
      </td>
      <td>
        <Checkbox
          name=""
          checked={variable.isSensitiveData}
          onChange={e => onValueChanged({target: {name: isSensitiveData, value: e.target.value}})}
        />
      </td>
      <td>
        <TextInput name="initialValue" value={variable.initialValue} onChange={onValueChanged} />
      </td>
      <td>
        <TextInput name="dataFormat" value={variable.dataFormat} onChange={onValueChanged} />
      </td>
    </tr>
  );
};

const VariablesTable = ({variables, editable, onChange, onDelete}) => {
  return (
    <table className="variables-table">
      <thead>
        <tr>
          {editable && <th className="variables-table__header" />}
          <th className="variables-table__header">
            <FormattedMessage defaultMessage="Name" description="Variable table name title" />
          </th>
          <th className="variables-table__header">
            <FormattedMessage defaultMessage="Key" description="Variable table key title" />
          </th>
          <th className="variables-table__header">
            <FormattedMessage
              defaultMessage="Prefill plugin"
              description="Variable table prefill plugin title"
            />
          </th>
          <th className="variables-table__header">
            <FormattedMessage
              defaultMessage="Prefill attribute"
              description="Variable table prefill attribute title"
            />
          </th>
          <th className="variables-table__header">
            <FormattedMessage
              defaultMessage="Data type"
              description="Variable table data type title"
            />
          </th>
          <th className="variables-table__header">
            <FormattedMessage
              defaultMessage="Sensitive data"
              description="Variable table sensitive data title"
            />
          </th>
          <th className="variables-table__header">
            <FormattedMessage
              defaultMessage="Initial value"
              description="Variable table initial value title"
            />
          </th>
          <th className="variables-table__header">
            <FormattedMessage
              defaultMessage="Data format"
              description="Variable table data format title"
            />
          </th>
        </tr>
      </thead>

      <tbody>
        {variables.map(variable =>
          editable ? (
            <EditableVariableRow
              key={variable.key}
              variable={variable}
              onChange={onChange}
              onDelete={onDelete}
            />
          ) : (
            <VariableRow key={variable.key} variable={variable} />
          )
        )}
      </tbody>
    </table>
  );
};

export default VariablesTable;
