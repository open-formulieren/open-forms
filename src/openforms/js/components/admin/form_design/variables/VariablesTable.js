import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';
import {get} from 'utils/fetch';

import DeleteIcon from 'components/admin/DeleteIcon';
import FAIcon from 'components/admin/FAIcon';
import {FormContext} from 'components/admin/form_design/Context';
import LiteralValueInput from 'components/admin/form_design/logic/LiteralValueInput';
import Field from 'components/admin/forms/Field';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';

import {DATATYPES_CHOICES, IDENTIFIER_ROLE_CHOICES} from './constants';
import RegistrationSummaryList from './registration';
import Variable from './types';
import {variableHasErrors} from './utils';

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

const Td = ({variable, fieldName}) => {
  const intl = useIntl();

  const field = variable[fieldName];
  let fieldErrors = variable.errors ? variable.errors[fieldName] : [];

  if (!Array.isArray(fieldErrors)) fieldErrors = [fieldErrors];

  fieldErrors = fieldErrors.map(error => {
    if (typeof error !== 'string' && error.defaultMessage) {
      return intl.formatMessage(error);
    }
    return error;
  });

  return (
    <td>
      <Field name={fieldName} errors={fieldErrors}>
        <div>{field}</div>
      </Field>
    </td>
  );
};

Td.propTypes = {
  variable: Variable.isRequired,
  fieldName: PropTypes.string.isRequired,
};

const VariableRow = ({index, variable, onFieldChange}) => {
  const intl = useIntl();
  const formContext = useContext(FormContext);
  const formSteps = formContext.formSteps;

  const getFormDefinitionName = formDefinition => {
    for (const step of formSteps) {
      if (step.formDefinition === formDefinition || step._generatedId === formDefinition)
        return step.name;
    }
    return '';
  };

  const rowClassnames = classNames(`row${(index % 2) + 1}`, 'variables-table__row', {
    'variables-table__row--errors': variableHasErrors(variable),
  });

  return (
    <tr className={rowClassnames}>
      <td />
      <td>{variable.name}</td>
      <Td variable={variable} fieldName="key" />
      <td>{getFormDefinitionName(variable.formDefinition)}</td>
      <td>{variable.prefillPlugin}</td>
      <td>{variable.prefillAttribute}</td>
      <td>
        {intl.formatMessage(
          IDENTIFIER_ROLE_CHOICES[variable.prefillIdentifierRole] || IDENTIFIER_ROLE_CHOICES.main
        )}
      </td>
      <td>
        <RegistrationSummaryList variable={variable} onFieldChange={onFieldChange} />
      </td>
      <td>{variable.dataType}</td>
      <td>
        <SensitiveData isSensitive={variable.isSensitiveData} />
      </td>
      <td>{JSON.stringify(variable.initialValue)}</td>
    </tr>
  );
};

const EditableVariableRow = ({index, variable, onDelete, onChange, onFieldChange}) => {
  const intl = useIntl();
  const deleteConfirmMessage = intl.formatMessage({
    description: 'User defined variable deletion confirm message',
    defaultMessage: 'Are you sure you want to delete this variable?',
  });

  const formContext = useContext(FormContext);

  const {availablePrefillPlugins} = formContext.plugins;
  const prefillPluginChoices = availablePrefillPlugins.map(plugin => [plugin.id, plugin.label]);
  const [prefillAttributeChoices, setPrefillAttributeChoices] = useState([]);

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

    const url = `/api/v2/prefill/plugins/${variable.prefillPlugin}/attributes`;
    const response = await get(url);
    if (!response.ok) {
      console.error(response.data);
    }

    setPrefillAttributeChoices(response.data.map(attribute => [attribute.id, attribute.label]));
  }, [variable.prefillPlugin]);

  // Cast booleans to strings, otherwise they don't display properly in the select widget
  const initialValue =
    variable.dataType === 'boolean' && typeof variable.initialValue == 'boolean'
      ? JSON.stringify(variable.initialValue)
      : variable.initialValue;

  return (
    <tr
      className={classNames('variables-table__row', `row${(index % 2) + 1}`, {
        'variables-table__row--errors': variableHasErrors(variable),
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
        <Field name="prefillPlugin" errors={variable.errors?.prefillPlugin}>
          <Select
            name="prefillPlugin"
            choices={prefillPluginChoices}
            value={variable.prefillPlugin || ''}
            onChange={onValueChanged}
            allowBlank
          />
        </Field>
      </td>
      <td>
        <Field name="prefillAttribute" errors={variable.errors?.prefillAttribute}>
          <Select
            name="prefillAttribute"
            choices={prefillAttributeChoices}
            value={variable.prefillAttribute || ''}
            onChange={onValueChanged}
            disabled={loading || !variable.prefillPlugin}
          />
        </Field>
      </td>
      <td>
        <Field name="prefillIdentifierRole" errors={variable.errors?.prefillIdentifierRole}>
          <Select
            name="prefillIdentifierRole"
            choices={Object.entries(IDENTIFIER_ROLE_CHOICES)}
            value={variable.prefillIdentifierRole || 'main'}
            onChange={onValueChanged}
            translateChoices
          />
        </Field>
      </td>
      <td>
        <RegistrationSummaryList variable={variable} onFieldChange={onFieldChange} />
      </td>
      <td>
        <Field name="dataType" errors={variable.errors?.dataType}>
          <Select
            name="dataType"
            choices={DATATYPES_CHOICES}
            translateChoices
            value={variable.dataType || ''}
            onChange={onValueChanged}
          />
        </Field>
      </td>
      <td>
        <Field name="isSensitiveData" errors={variable.errors?.isSensitiveData}>
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
        <Field name="initialValue" errors={variable.errors?.initialValue}>
          <LiteralValueInput
            key={`initialValue-${index}`}
            name="initialValue"
            type={variable.dataType}
            value={initialValue}
            onChange={onValueChanged}
          />
        </Field>
      </td>
    </tr>
  );
};

const VariablesTable = ({variables, editable, onDelete, onChange, onFieldChange}) => {
  const headColumns = (
    <>
      <HeadColumn content="" />
      <HeadColumn
        content={<FormattedMessage defaultMessage="Name" description="Variable table name title" />}
      />
      <HeadColumn
        content={<FormattedMessage defaultMessage="Key" description="Variable table key title" />}
      />
      {!editable && (
        <HeadColumn
          content={
            <FormattedMessage
              defaultMessage="Form definition"
              description="Variable table form definition title"
            />
          }
        />
      )}
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
            defaultMessage="Prefill identifier role"
            description="Variable table identifier role attribute title"
          />
        }
      />
      <HeadColumn
        content={
          <FormattedMessage
            defaultMessage="Registration"
            description="Variable table registration title"
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
    </>
  );

  return (
    <div className="variables-table">
      <ChangelistTableWrapper headColumns={headColumns} extraModifiers={['fixed']}>
        {variables.map((variable, index) =>
          editable ? (
            <EditableVariableRow
              key={`${variable.key}-${index}`}
              index={index}
              variable={variable}
              onDelete={onDelete}
              onChange={onChange}
              onFieldChange={onFieldChange}
            />
          ) : (
            <VariableRow
              key={`${variable.key}-${index}`}
              index={index}
              variable={variable}
              onFieldChange={onFieldChange}
            />
          )
        )}
      </ChangelistTableWrapper>
    </div>
  );
};

export default VariablesTable;
