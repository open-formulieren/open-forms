import classNames from 'classnames';
import groupBy from 'lodash/groupBy';
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

const KeyDisplay = ({variable}) => {
  const intl = useIntl();

  let fieldErrors = variable?.errors?.key ?? [];

  if (!Array.isArray(fieldErrors)) fieldErrors = [fieldErrors];

  fieldErrors = fieldErrors.map(error => {
    if (typeof error !== 'string' && error.defaultMessage) {
      return intl.formatMessage(error);
    }
    return error;
  });

  return (
    <Field name="key" errors={fieldErrors}>
      <code>{variable.key}</code>
    </Field>
  );
};

KeyDisplay.propTypes = {
  variable: Variable.isRequired,
};

const VariableRow = ({variable, onFieldChange}) => {
  const rowClassnames = classNames('variables-table__row', {
    'variables-table__row--errors': variableHasErrors(variable),
  });

  return (
    <tr className={rowClassnames}>
      <td />
      <td>{variable.name}</td>
      <td>
        <KeyDisplay variable={variable} fieldName="key" />
      </td>
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
      className={classNames('variables-table__row', {
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
          options={variable.prefillOptions}
          onChange={({plugin, attribute, identifierRole, options}) =>
            onChange(variable.key, '', {
              prefillPlugin: plugin,
              prefillAttribute: attribute,
              prefillIdentifierRole: identifierRole,
              prefillOptions: options,
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
        <Field
          name="initialValue"
          errors={variable.errors?.initialValue}
          extraModifiers={['flex-wrap']}
        >
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
  const {formSteps} = useContext(FormContext);

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

  // first, sort the variables alphabetically
  const sortedVariables = variables.toSorted((var1, var2) => var1.name.localeCompare(var2.name));
  // then, group the variables by their step so that we display them grouped in the table,
  // which cuts down on the number of columns to display
  const variablesGroupedByFormStep = groupBy(
    sortedVariables,
    variable => variable.formDefinition ?? ''
  );

  // convert back to an ordered array, in order of steps, as Objects don't have a
  // guaranteed insert order
  const variableGroups = formSteps.map(step => {
    const key = step.formDefinition || step._generatedId;
    return [step, variablesGroupedByFormStep?.[key]];
  });
  // and add the variables not attached to a step (the user defined vars)
  const varsNotRelatedToStep = variablesGroupedByFormStep[''];
  if (varsNotRelatedToStep) {
    variableGroups.push([{name: '', _generatedId: 'userDefined'}, varsNotRelatedToStep]);
  }

  return (
    <div className="variables-table">
      <ChangelistTableWrapper headColumns={headColumns} extraModifiers={['fixed']}>
        {variableGroups.map(
          ([step, stepVariables]) =>
            stepVariables && (
              <React.Fragment key={step.uuid || step._generatedId}>
                {step.name && (
                  <tr>
                    <td />
                    <th colSpan={7} className="variables-table__step-name">
                      {step.name}
                    </th>
                  </tr>
                )}
                {stepVariables.map((variable, index) =>
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
                      variable={variable}
                      onFieldChange={onFieldChange}
                    />
                  )
                )}
              </React.Fragment>
            )
        )}
      </ChangelistTableWrapper>
    </div>
  );
};

export default VariablesTable;
