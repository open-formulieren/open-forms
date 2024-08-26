import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import LiteralValueInput from 'components/admin/form_design/logic/LiteralValueInput';
import Field from 'components/admin/forms/Field';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {DeleteIcon, FAIcon} from 'components/admin/icons';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';

import {DATATYPES_CHOICES} from './constants';
import {PrefillSummary} from './prefill';
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
  let fieldErrors = variable?.errors?.[fieldName] ?? [];

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
      <td>
        <PrefillSummary
          plugin={variable.prefillPlugin}
          attribute={variable.prefillAttribute}
          identifierRole={variable.prefillIdentifierRole}
          errors={variable.errors}
        />
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

  const onValueChanged = e => {
    onChange(variable.key, e.target.name, e.target.value);
  };

  const updateKey = e => {
    // Key creation taken from FormIO
    let updatedKey = _.camelCase(variable.name).replace(/^[0-9]*/, '');
    onChange(variable.key, 'key', updatedKey);
  };

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
        <PrefillSummary
          plugin={variable.prefillPlugin}
          attribute={variable.prefillAttribute}
          identifierRole={variable.prefillIdentifierRole}
          errors={variable.errors}
          prefillOptions={variable.prefillOptions}
          onChange={({plugin, attribute, identifierRole}) =>
            onChange(variable.key, '', {
              prefillPlugin: plugin,
              prefillAttribute: attribute,
              prefillIdentifierRole: identifierRole,
            })
          }
        />
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
          <FormattedMessage defaultMessage="Prefill" description="Variable table prefill title" />
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
