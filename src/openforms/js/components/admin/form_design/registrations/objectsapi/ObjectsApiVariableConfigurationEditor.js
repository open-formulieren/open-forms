import {Form, Formik} from 'formik';
import isEqual from 'lodash/isEqual';
import React, {useContext, useEffect} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

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
 * @param {ObjectsAPIRegistrationBackend} p.setGetOptions - A callback to register the function that will return the edited options
 * @returns {JSX.Element} - The summary, represented as a the parts of the target path separated by '>'
 */
const ObjectsApiVariableConfigurationEditor = ({variable, backend, setGetOptions}) => {
  const {
    form: {uuid},
  } = useContext(FormContext);

  const getOptions = () => {
    return backend.options;
  };

  useEffect(() => {
    setGetOptions(() => getOptions);
  }, []);

  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(
    async () => {
      const response = await get(REGISTRATION_OBJECTS_TARGET_PATHS, {
        backendKey: backend.key,
        formUuid: uuid,
        variableKey: variable.key,
      });

      if (!response.ok) {
        throw new Error('Loading available target paths failed');
      }

      return response.data;
    },
    // Load only once:
    []
  );

  const getTargetPath = pathSegment =>
    targetPaths.find(t => isEqual(t.targetPath, JSON.parse(pathSegment)));

  const choices =
    loading || error
      ? LOADING_OPTION
      : targetPaths.map(t => [
          JSON.stringify(t.targetPath),
          `${t.targetPath.join(' > ')}${t.required ? ' (required)' : ''}`,
        ]);

  return (
    <Formik
      initialValues={{
        targetPath: JSON.stringify(
          (
            backend.options.variablesMapping.find(
              mapping => mapping.variableKey === variable.key
            ) || backend.options.variablesMapping[0]
          ).targetPath
        ),
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
                  <pre>
                    {loading
                      ? 'N/A'
                      : JSON.stringify(getTargetPath(formik.values.targetPath).jsonSchema, null, 2)}
                  </pre>
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
