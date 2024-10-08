import {useField, useFormikContext} from 'formik';
import {useContext} from 'react';
import useUpdateEffect from 'react-use/esm/useUpdateEffect';

import {FormContext} from 'components/admin/form_design/Context';
import Select from 'components/admin/forms/Select';

const PluginField = () => {
  const [fieldProps] = useField('plugin');
  const {setFieldValue} = useFormikContext();
  const {
    plugins: {availablePrefillPlugins},
  } = useContext(FormContext);

  const {value} = fieldProps;

  // reset the attribute value whenever the plugin changes
  useUpdateEffect(() => {
    setFieldValue('attribute', '');
  }, [setFieldValue, value]);

  const choices = availablePrefillPlugins.map(plugin => [plugin.id, plugin.label]);
  return <Select allowBlank choices={choices} id="id_plugin" {...fieldProps} />;
};

export default PluginField;
