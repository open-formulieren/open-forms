import {Form, Formik} from 'formik';
import isEqual from 'lodash/isEqual';
import React, {useContext, useEffect} from 'react';
import {FormattedMessage} from 'react-intl';
import {useAsync, useToggle} from 'react-use';

import {FormContext} from 'components/admin/form_design/Context';
import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
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

  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);

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
          <Fieldset>
            <FormRow>
              <Field
                name="name"
                label={
                  <FormattedMessage
                    description="'Variable key' label"
                    defaultMessage="Variable key"
                  />
                }
              >
                <div className="readonly">{variable.key}</div>
              </Field>
            </FormRow>
            <FormRow>
              <Field
                name="targetPath"
                htmlFor="targetPath"
                label={
                  <FormattedMessage
                    defaultMessage="JSON Schema target"
                    description="'JSON Schema target' label"
                  />
                }
              >
                <Select
                  id="targetPath"
                  name="targetPath"
                  allowBlank
                  choices={choices}
                  {...formik.getFieldProps('targetPath')}
                />
              </Field>
            </FormRow>
            <div style={{marginTop: '1em'}}>
              <a href="#" onClick={e => e.preventDefault() || toggleJsonSchemaVisible()}>
                <FormattedMessage
                  description="Objects API variable configuration editor JSON Schema visibility toggle"
                  defaultMessage="Toggle JSON Schema"
                />
              </a>
              {jsonSchemaVisible && (
                <pre>
                  {loading || !formik.values.targetPath
                    ? 'N/A'
                    : JSON.stringify(getTargetPath(formik.values.targetPath).jsonSchema, null, 2)}
                </pre>
              )}
            </div>
          </Fieldset>
        </Form>
      )}
    </Formik>
  );
};

export default ObjectsApiVariableConfigurationEditor;
