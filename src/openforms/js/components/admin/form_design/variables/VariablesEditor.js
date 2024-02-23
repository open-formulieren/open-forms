import React from 'react';
import {FormattedMessage} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import Tab from 'components/admin/form_design/Tab';
import Fieldset from 'components/admin/forms/Fieldset';

import StaticData from './StaticData';
import UserDefinedVariables from './UserDefinedVariables';
import VariablesTable from './VariablesTable';
import {VARIABLE_SOURCES} from './constants';
import {variableHasErrors} from './utils';

const VariablesEditor = ({variables, onAdd, onDelete, onChange, onFieldChange}) => {
  const userDefinedVariables = variables.filter(
    variable => variable.source === VARIABLE_SOURCES.userDefined
  );

  const componentVariables = variables.filter(
    variable => variable.source === VARIABLE_SOURCES.component
  );

  return (
    <Fieldset
      title={
        <FormattedMessage
          defaultMessage="Form variables configuration"
          description="Form variables configuration editor fieldset title"
        />
      }
      extraClassName="variables-editor"
    >
      <div className="variables-editor__tabs">
        <Tabs>
          <TabList>
            <Tab hasErrors={componentVariables.some(variable => variableHasErrors(variable))}>
              <FormattedMessage
                defaultMessage="Component"
                description="Component variables tab title"
              />
            </Tab>
            <Tab hasErrors={userDefinedVariables.some(variable => variableHasErrors(variable))}>
              <FormattedMessage
                defaultMessage="User defined"
                description="User defined variables tab title"
              />
            </Tab>
            <Tab>
              <FormattedMessage defaultMessage="Static" description="Static variables tab title" />
            </Tab>
          </TabList>

          <TabPanel>
            <VariablesTable variables={componentVariables} onFieldChange={onFieldChange} />
          </TabPanel>
          <TabPanel>
            <UserDefinedVariables
              variables={userDefinedVariables}
              onAdd={onAdd}
              onDelete={onDelete}
              onChange={onChange}
              onFieldChange={onFieldChange}
            />
          </TabPanel>
          <TabPanel>
            <StaticData />
          </TabPanel>
        </Tabs>
      </div>
    </Fieldset>
  );
};

export default VariablesEditor;
