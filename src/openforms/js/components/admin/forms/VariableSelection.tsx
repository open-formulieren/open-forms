import classNames from 'classnames';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';
import {components} from 'react-select';
import type {OptionProps} from 'react-select';

import {FormContext} from 'components/admin/form_design/Context';
import {
  getVariableSourceLabel,
  groupVariablesBySource,
} from 'components/admin/form_design/variables/utils';

import {FieldChangeEvent, FormVariable} from '@/components/types';

import {SelectWithoutFormik} from './ReactSelect';

interface VariableData {
  value: any;
  label: string;
  formDefinitionName: string;
}
interface VariableOptionProps extends OptionProps {
  data: VariableData;
}

const VariableOption: React.FC<VariableOptionProps> = props => {
  const {value, label, formDefinitionName} = props.data;
  return (
    <components.Option {...props}>
      <span
        className={classNames('form-variable-dropdown-option', {
          'form-variable-dropdown-option--component-variable': !!formDefinitionName,
        })}
      >
        <span className="form-variable-dropdown-option__label">{label}</span>

        <code className="form-variable-dropdown-option__key">{value}</code>

        {formDefinitionName && (
          <span className="form-variable-dropdown-option__form-definition">
            {formDefinitionName}
          </span>
        )}
      </span>
    </components.Option>
  );
};

const allowAny = () => true;

interface VariableSelectionProps {
  id: string;
  name: string;
  value: string | string[];
  onChange: (event: FieldChangeEvent) => void;
  includeStaticVariables?: boolean;
  filter?: (...args: any[]) => boolean;
}

type VariableSource = 'component' | 'user_defined' | 'static';
interface VariableGroup {
  source: VariableSource;
  variables: FormVariable[];
}

const VariableSelection: React.FC<VariableSelectionProps> = ({
  id,
  name,
  value,
  onChange,
  includeStaticVariables = false,
  filter = allowAny,
  ...props
}) => {
  const {formSteps, formVariables, staticVariables} = useContext(FormContext);
  const intl = useIntl();

  let formDefinitionsNames: Record<string, string> = {};
  formSteps.forEach(step => {
    const formDefinitionsIndex = step.formDefinition || step._generatedId;
    if (!formDefinitionsIndex) {
      throw Error('Unable to determine an index for step');
    }
    formDefinitionsNames[formDefinitionsIndex] = step.internalName || step.name;
  });

  const allFormVariables = (includeStaticVariables ? staticVariables : []).concat(formVariables);
  const relevantVariables = allFormVariables.filter(variable => filter(variable));

  const choices = groupVariablesBySource(relevantVariables).map((variableGroup: VariableGroup) => ({
    label: intl.formatMessage(getVariableSourceLabel(variableGroup.source)),
    options: variableGroup.variables.map(variable => ({
      label: variable.name,
      value: variable.key,
      formDefinitionName: variable.formDefinition
        ? formDefinitionsNames[variable.formDefinition]
        : undefined,
    })),
  }));

  return (
    <SelectWithoutFormik
      id={id}
      className="form-variable-dropdown"
      name={name}
      options={choices}
      onChange={(newValue: string) => onChange({target: {name, value: newValue}})}
      components={{Option: VariableOption}}
      value={value}
      {...props}
    />
  );
};

export default VariableSelection;
