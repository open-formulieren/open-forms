import React from 'react';
import {FormattedMessage} from 'react-intl';

import Select from 'components/admin/forms/Select';

/**
 * Returns the Objects API Configuration editor modal for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   variablesMapping: {variableKey: string, targetPath: string[]}[]
 * }} ObjectsAPIV2Options
 *
 * @param {Object} p
 * @param {string} p.variable - The current variable
 * @param {ObjectsAPIV2Options} p.backendOptions - The Objects API Options (guaranteed to be v2)
 * @returns {JSX.Element} - The summary, represented as a the parts of the target path separated by '>'
 */
const ObjectsApiVariableConfigurationEditor = ({variable, backendOptions}) => {
  return (
    <table>
      <thead>
        <tr>
          <th>
            <FormattedMessage defaultMessage="Variable name" description="'Variable name' label" />
          </th>
          <th>
            <FormattedMessage defaultMessage="Variable key" description="'Variable key' label" />
          </th>
          <th>
            <FormattedMessage
              defaultMessage="JSON Schema target"
              description="'JSON Schema target' label"
            />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>{variable.name}</td>
          <td>{variable.key}</td>
          <td>
            <Select choices={[['test', 'test']]} />
          </td>
        </tr>
      </tbody>
    </table>
  );
};

export default ObjectsApiVariableConfigurationEditor;
