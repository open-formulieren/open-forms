export function getContextComponentsWithType(context, type) {
  // Copied from https://github.com/formio/formio.js/blob/v4.13.0/src/utils/utils.js#L1092-L1105 and modified
  //   so we can also filter on types
  const values = [];

  context.utils.eachComponent(context.instance.options.editForm.components, (component, path) => {
    if (component.key !== context.data.key && component.type === type) {
      values.push({
        label: `${component.label || component.key} (${path})`,
        value: path,
      });
    }
  });

  return values;
}
