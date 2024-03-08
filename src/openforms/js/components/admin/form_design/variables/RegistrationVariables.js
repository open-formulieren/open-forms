import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import Fieldset from 'components/admin/forms/Fieldset';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';

import RegistrationSummaryList from './registration';

const PluginVariables = ({
  headColumns,
  registrationPlugin,
  registrationBackends,
  onFieldChange,
}) => (
  <ChangelistTableWrapper headColumns={headColumns} extraModifiers={['fixed']}>
    {registrationPlugin.pluginVariables.map((variable, index) => {
      return (
        <tr className={`row${(index % 2) + 1}`} key={variable.key}>
          <td />
          <td>{variable.name}</td>
          <td>{variable.key}</td>
          <td>
            <RegistrationSummaryList
              variable={variable}
              onFieldChange={onFieldChange}
              registrationBackends={registrationBackends.filter(
                b => b.backend === registrationPlugin.pluginIdentifier
              )}
            />
          </td>
          <td>{variable.dataType}</td>
        </tr>
      );
    })}
  </ChangelistTableWrapper>
);

const RegistrationVariables = ({onFieldChange}) => {
  const formContext = useContext(FormContext);
  const registrationBackends = formContext.registrationBackends;
  const registrationPluginsVariables = formContext.registrationPluginsVariables.filter(
    plugin =>
      registrationBackends.some(b => b.backend === plugin.pluginIdentifier) &&
      plugin.pluginVariables.length
  );

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
    </>
  );

  return (
    <div className="variables-table">
      {registrationPluginsVariables.map((registrationPlugin, index) => {
        const pluginVariables = (
          <PluginVariables
            headColumns={headColumns}
            registrationPlugin={registrationPlugin}
            registrationBackends={registrationBackends}
            onFieldChange={onFieldChange}
          />
        );

        if (registrationPluginsVariables.length === 1) return pluginVariables;

        return (
          <Fieldset title={registrationPlugin.pluginVerboseName} key={index}>
            {pluginVariables}
          </Fieldset>
        );
      })}
    </div>
  );
};

export default RegistrationVariables;
