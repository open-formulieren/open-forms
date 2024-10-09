import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';
import {components} from 'react-select';

import {FormContext} from 'components/admin/form_design/Context';
import {
  getVariableSourceLabel,
  groupVariablesBySource,
} from 'components/admin/form_design/variables/utils';

import {SelectWithoutFormik} from './ReactSelect';

const allowAny = () => true;

const VariableSelection = ({
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

  let formDefinitionsNames = {};
  formSteps.forEach(step => {
    formDefinitionsNames[step.formDefinition || step._generatedId] = step.internalName || step.name;
  });

  const allFormVariables = (includeStaticVariables ? staticVariables : []).concat(formVariables);

  const choices = groupVariablesBySource(allFormVariables.filter(variable => filter(variable))).map(
    variableGroup => ({
      label: intl.formatMessage(getVariableSourceLabel(variableGroup.source)),
      options: variableGroup.variables.map(variable => ({
        label: variable.name,
        value: variable.key,
        variable: variable,
      })),
    })
  );

  const OptionComponent = props => {
    const {variable} = props.data;
    return (
      <components.Option {...props}>
        <span className="form-variable-dropdown__option">
          <span className="form-variable-dropdown__option__label">
            {variable.name}{' '}
            <code className="form-variable-dropdown__option__key">({variable.key})</code>
          </span>
          {formDefinitionsNames[variable.formDefinition] && (
            <span className="form-variable-dropdown__option__form-definition">
              {formDefinitionsNames[variable.formDefinition]}
            </span>
          )}
        </span>
      </components.Option>
    );
  };

  return (
    <SelectWithoutFormik
      id={id}
      className="form-variable-dropdown"
      name={name}
      options={choices}
      onChange={newValue => onChange({target: {name, value: newValue}})}
      components={{Option: OptionComponent}}
      value={value}
      {...props}
    />
  );
};

VariableSelection.propTypes = {
  id: PropTypes.string,
  name: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  includeStaticVariables: PropTypes.bool,
  filter: PropTypes.func,
};

export default VariableSelection;
