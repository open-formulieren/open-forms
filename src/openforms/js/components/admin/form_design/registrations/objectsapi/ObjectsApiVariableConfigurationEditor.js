import {Form, Formik} from 'formik';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import Select from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

// TODO: properly translate this
const LOADING_OPTION = [['...', 'loading...']];

/**
 * Returns the Objects API Configuration editor modal for a specific variable. This only applies to V2 Options
 *
 * @typedef {{
 *   backend: string;
 *   key: string;
 *   name: string;
 *   options: {
 *     variablesMapping: {variableKey: string, targetPath: string[]}[]
 *   }
 * }} ObjectsAPIRegistrationBackend
 *
 * @param {Object} p
 * @param {Object} p.variable - The current variable
 * @param {ObjectsAPIRegistrationBackend} p.backend - The Objects API registration backend (options guaranteed to be v2)
 * @returns {JSX.Element} - The summary, represented as a the parts of the target path separated by '>'
 */
const ObjectsApiVariableConfigurationEditor = ({variable, backend}) => {
  const {
    form: {uuid},
  } = useContext(FormContext);

  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(async () => {
    const response = await get('/api/v2/registration/plugins/objects-api/target-paths', {
      backendKey: backend.key,
      formUuid: uuid,
      variableKey: variable.key,
    });

    if (!response.ok) {
      throw new Error('Loading available target paths failed');
    }

    return response.data;
  }, []);

  const choices =
    loading || error
      ? LOADING_OPTION
      : targetPaths.map(t => [t.targetPath, t.targetPath.join(' > ')]);

  return (
    <Formik
      initialValues={{
        targetPath:
          backend.options.variablesMapping.find(mapping => mapping.variableKey === variable.key)
            .targetPath || '',
      }}
    >
      {formik => (
        <Form>
          <table>
            <thead>
              <tr>
                <th>
                  <FormattedMessage
                    defaultMessage="Variable name"
                    description="'Variable name' label"
                  />
                </th>
                <th>
                  <FormattedMessage
                    defaultMessage="Variable key"
                    description="'Variable key' label"
                  />
                </th>
                <th>
                  <FormattedMessage
                    defaultMessage="JSON Schema target"
                    description="'JSON Schema target' label"
                  />
                </th>
                <th>
                  <FormattedMessage
                    defaultMessage="JSON Schema info"
                    description="'JSON Schema info' label"
                  />
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{variable.name}</td>
                <td>{variable.key}</td>
                <td>
                  <Select
                    id="targetPath"
                    name="targetPath"
                    choices={choices}
                    {...formik.getFieldProps('targetPath')}
                  />
                </td>
                <td>
                  <pre>{JSON.stringify({}, null, 2)}</pre>
                </td>
              </tr>
            </tbody>
          </table>
        </Form>
      )}
    </Formik>
  );
};

export default ObjectsApiVariableConfigurationEditor;
