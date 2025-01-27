import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import {FormContext} from 'components/admin/form_design/Context';
import Tab from 'components/admin/form_design/Tab';
import Fieldset from 'components/admin/forms/Fieldset';

import RegistrationVariables from './RegistrationVariables';
import StaticData from './StaticData';
import UserDefinedVariables from './UserDefinedVariables';
import VariablesTable from './VariablesTable';
import {VARIABLE_SOURCES, VARIABLE_SOURCES_GROUP_LABELS} from './constants';
import {variableHasErrors} from './utils';

const VariablesEditor = ({variables, onAdd, onDelete, onChange, onFieldChange}) => {
  const intl = useIntl();
  const {staticVariables} = useContext(FormContext);
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
              {intl.formatMessage(VARIABLE_SOURCES_GROUP_LABELS.component)} (
              {componentVariables.length})
            </Tab>
            <Tab hasErrors={userDefinedVariables.some(variable => variableHasErrors(variable))}>
              {intl.formatMessage(VARIABLE_SOURCES_GROUP_LABELS.userDefined)} (
              {userDefinedVariables.length})
            </Tab>
            <Tab>
              {intl.formatMessage(VARIABLE_SOURCES_GROUP_LABELS.static)} ({staticVariables.length})
            </Tab>
            <Tab>
              <FormattedMessage
                defaultMessage="Registration"
                description="Registration variables tab title"
              />
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
            <StaticData onFieldChange={onFieldChange} />
          </TabPanel>
          <TabPanel>
            <RegistrationVariables onFieldChange={onFieldChange} />
          </TabPanel>
        </Tabs>
      </div>
    </Fieldset>
  );
};

export default VariablesEditor;
