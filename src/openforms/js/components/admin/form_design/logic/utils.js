const updateWarningsValidationError = (
  validationErrors,
  tabsWithErrors,
  fieldName,
  index,
  name,
  tabName
) => {
  validationErrors = validationErrors.filter(
    ([key]) => !key.startsWith(`${fieldName}.${index}.${name}`)
  );
  // Update the error badge in the tabs
  const errors = validationErrors.filter(([key]) => key.startsWith(fieldName));
  if (!errors.length) {
    tabsWithErrors = tabsWithErrors.filter(tabId => tabId !== tabName);
  }
  return [validationErrors, tabsWithErrors];
};

export {updateWarningsValidationError};
