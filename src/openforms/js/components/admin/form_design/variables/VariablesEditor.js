import React from 'react';
import {TabList, TabPanel, Tabs} from 'react-tabs';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import Tab from 'components/admin/form_design/Tab';

import {VARIABLE_SOURCES} from './constants';
import UserDefinedVariables from './UserDefinedVariables';
import VariablesTable from './VariablesTable';
import StaticData from './StaticData';

const VariablesEditor = ({variables, onAdd, onChange, onDelete}) => {
  const userDefinedVariables = variables.filter(
    variable => variable.source === VARIABLE_SOURCES.userDefined
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
            <Tab>
              <FormattedMessage
                defaultMessage="Component"
                description="Component variables tab title"
              />
            </Tab>
            <Tab
              hasErrors={userDefinedVariables.some(
                variable => Object.entries(variable.errors || {}).length
              )}
            >
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
            <VariablesTable
              variables={variables.filter(
                variable => variable.source === VARIABLE_SOURCES.component
              )}
            />
          </TabPanel>
          <TabPanel>
            <UserDefinedVariables
              variables={variables.filter(
                variable => variable.source === VARIABLE_SOURCES.userDefined
              )}
              onAdd={onAdd}
              onDelete={onDelete}
              onChange={onChange}
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
