/**
 * Translate the array-based files options to a mapping that's easier to process
 * on the client side.
 */
export const optionsToFormikValues = options => {
  const updatedFiles = Object.fromEntries(
    (options.files ?? []).map(({key, ...overrides}) => [key, overrides])
  );
  return {
    ...options,
    files: updatedFiles,
  };
};

/**
 * Translate the array-based file component options to an array of options so that
 * the backend doesn't mangle the component keys when applying the camelCase to
 * snake_case conversion.
 */
export const formikValuesToOptions = values => {
  const updatedFiles = Object.entries(values.files ?? {}).map(([key, overrides]) => ({
    key,
    ...overrides,
  }));
  return {
    ...values,
    files: updatedFiles,
  };
};
