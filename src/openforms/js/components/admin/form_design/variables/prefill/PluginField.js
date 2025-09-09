import {useField, useFormikContext} from 'formik';
import {useContext} from 'react';
import {FormattedMessage} from 'react-intl';
import useUpdateEffect from 'react-use/esm/useUpdateEffect';

import MessageList from 'components/admin/MessageList';
import {FormContext} from 'components/admin/form_design/Context';
import {getPluginWarnings} from 'components/admin/form_design/PluginWarning';
import Select from 'components/admin/forms/Select';

const PluginField = () => {
  const [fieldProps] = useField('plugin');
  const {setFieldValue} = useFormikContext();
  const {
    plugins: {availablePrefillPlugins, availableAuthPlugins, selectedAuthPlugins},
  } = useContext(FormContext);

  const {value} = fieldProps;

  // reset the attribute value whenever the plugin changes
  useUpdateEffect(() => {
    setFieldValue('attribute', '');
  }, [setFieldValue, value]);

  // check if we need to display any warnings
  const prefillPlugin = availablePrefillPlugins.find(plugin => plugin.id === value);
  const authWarnings = getPluginWarnings(prefillPlugin, availableAuthPlugins, selectedAuthPlugins);

  const warnings = authWarnings.map(({type, ...rest}) => {
    switch (type) {
      case 'authAttribute': {
        const {requiresAuth} = rest;
        return (
          <FormattedMessage
            description="Prefill plugin requires unavailable auth attribute warning"
            defaultMessage={`{plugin} requires one of the "{requiredAuthAttribute}" attributes.
              Please select one or more authentication plugins that provide such an attribute.`}
            values={{
              plugin: prefillPlugin.label,
              requiredAuthAttribute: requiresAuth.join(', '),
            }}
          />
        );
      }
      case 'authPlugin': {
        const {requiredPlugin} = rest;
        return (
          <FormattedMessage
            description="Prefill plugin requires unavailable auth plugin warning"
            defaultMessage={`{plugin} requires one of the "{requiredPlugin}"
              login options. Please select one or remove the prefill plugin.`}
            values={{
              plugin: prefillPlugin.label,
              requiredPlugin: requiredPlugin.join(', '),
            }}
          />
        );
      }
    }
  });

  const choices = availablePrefillPlugins.map(plugin => [plugin.id, plugin.label]);
  return (
    <div>
      <Select allowBlank choices={choices} id="id_plugin" {...fieldProps} />
      <MessageList messages={warnings.map(warning => ({level: 'warning', message: warning}))} />
    </div>
  );
};

export default PluginField;
