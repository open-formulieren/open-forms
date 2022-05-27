import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import {Checkbox, TextInput} from '../../forms/Inputs';
import Select from '../../forms/Select';
import {DATATYPES_CHOICES} from './constants';
import DeleteIcon from '../../DeleteIcon';
import {FormStepsContext, PluginsContext} from '../Context';
import {get} from '../../../../utils/fetch';
import FAIcon from '../../FAIcon';
import {ChangelistTableWrapper, HeadColumn} from '../../tables';

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
  const formSteps = useContext(FormStepsContext);

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
      <td>{variable.initialValue}</td>
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

  const {availablePrefillPlugins} = useContext(PluginsContext);
  const prefillPluginChoices = availablePrefillPlugins.map(plugin => [plugin.id, plugin.label]);
  const [prefillAttributeChoices, setPrefillAttributeChoices] = useState([]);

  const formSteps = useContext(FormStepsContext);
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

  return (
    <tr className={`row${(index % 2) + 1}`}>
      <td>
        <DeleteIcon onConfirm={() => onDelete(variable.key)} message={deleteConfirmMessage} />
      </td>
      <td>
        <TextInput
          name="name"
          value={variable.name}
          onChange={onValueChanged}
          onBlur={updateKey}
          noVTextField={true}
        />
      </td>
      <td>
        <TextInput name="key" value={variable.key} noVTextField={true} disabled={true} />
      </td>
      <td>
        <Select
          name="formDefinition"
          choices={formStepsChoices}
          value={variable.formDefinition}
          onChange={onValueChanged}
          allowBlank
        />
      </td>
      <td>
        <Select
          name="prefillPlugin"
          choices={prefillPluginChoices}
          value={variable.prefillPlugin}
          onChange={onValueChanged}
          allowBlank
        />
      </td>
      <td>
        <Select
          name="prefillAttribute"
          choices={prefillAttributeChoices}
          value={variable.prefillAttribute}
          onChange={onValueChanged}
          disabled={loading || !variable.prefillPlugin}
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
          label=""
          checked={variable.isSensitiveData}
          onChange={e =>
            onValueChanged({target: {name: 'isSensitiveData', value: !variable.isSensitiveData}})
          }
        />
      </td>
      <td>
        <TextInput
          name="initialValue"
          value={variable.initialValue || ''}
          onChange={onValueChanged}
          noVTextField={true}
        />
      </td>
      <td>
        <TextInput
          name="dataFormat"
          value={variable.dataFormat}
          onChange={onValueChanged}
          noVTextField={true}
        />
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
