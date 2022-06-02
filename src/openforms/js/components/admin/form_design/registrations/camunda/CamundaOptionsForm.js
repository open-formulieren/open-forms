import groupBy from 'lodash/groupBy';
import React from 'react';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {get} from '../../../../../utils/fetch';
import {PROCESS_DEFINITIONS_ENDPOINT, CAMUNDA_PLUGINS_ENDPOINT} from '../../constants';
import Field from '../../../forms/Field';
import Loader from '../../../Loader';
import FormFields from './FormFields';

const useLoadBackendData = () => {
  let processDefinitions;
  let plugins;
  const {loading, value, error} = useAsync(async () => {
    const [processDefinitionsResponse, pluginsResponse] = await Promise.all([
      get(PROCESS_DEFINITIONS_ENDPOINT),
      get(CAMUNDA_PLUGINS_ENDPOINT),
    ]);

    if (!processDefinitionsResponse.ok)
      throw new Error(`Response status: ${processDefinitionsResponse.status}`);
    if (!pluginsResponse.ok) throw new Error(`Response status: ${pluginsResponse.status}`);

    return [processDefinitionsResponse.data, pluginsResponse.data];
  }, []);

  if (!loading && !error) {
    // transform the process definitions in a grouped structure
    processDefinitions = groupBy(value[0], 'key');
    plugins = value[1];
  }

  return {loading, processDefinitions, plugins, error};
};

// TODO: handle validation errors properly
const CamundaOptionsForm = ({name, label, formData, onChange}) => {
  const {loading, processDefinitions, plugins, error} = useLoadBackendData();
  if (error) {
    console.error(error);
    return 'Unexpected error, see console';
  }
  return (
    <Field name={name} label={label} errors={[]}>
      {loading ? (
        <Loader />
      ) : (
        <FormFields
          formData={formData}
          onChange={formData => onChange({formData})}
          processDefinitions={processDefinitions}
          plugins={plugins}
        />
      )}
    </Field>
  );
};

CamundaOptionsForm.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.node.isRequired,
  formData: PropTypes.shape({
    // matches the backend serializer!
    processDefinition: PropTypes.string,
    processDefinitionVersion: PropTypes.number,
    processVariables: PropTypes.arrayOf(
      PropTypes.shape({
        enabled: PropTypes.bool.isRequired,
        componentKey: PropTypes.string.isRequired,
        alias: PropTypes.string.isRequired,
      })
    ),
    complexProcessVariables: PropTypes.arrayOf(PropTypes.object),
  }),
  onChange: PropTypes.func.isRequired,
};

export default CamundaOptionsForm;
