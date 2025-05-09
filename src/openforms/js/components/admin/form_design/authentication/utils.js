/**
 * Generating the configuration options for an authentication plugin, using its schema.
 *
 * plugin AuthPlugin
 */
const getInitialPluginOptions = plugin =>
  plugin?.schema
    ? Object.assign(
        {},
        Object.keys(plugin.schema.properties).map(propertyKey => ({
          [propertyKey]: plugin.schema.properties[propertyKey].default ?? '',
        }))
      )
    : null;

export {getInitialPluginOptions};
